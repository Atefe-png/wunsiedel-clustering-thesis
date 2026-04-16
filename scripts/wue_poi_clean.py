"""
============================================================
Data Quality Check & Deduplication — wue_final.gpkg
------------------------------------------------------------
Thesis: Clustering Methods for POI Aggregation in Rural Areas
Case Study: Landkreis Wunsiedel im Fichtelgebirge

Columns expected:
    osm_id, code, fclass, name, area_m2, layer, path,
    source, category, gfa_m2, type, attraction_weight

Steps:
    1. Basic dataset overview
    2. Missing values per column
    3. Duplicate detection (geometry + osm_id + fclass)
    4. Category & fclass distribution
    5. Outlier check (gfa_m2, attraction_weight, area_m2)
    6. Remove duplicates → save cleaned file
============================================================
"""

import geopandas as gpd
gdf = gpd.read_file("wue_final.gpkg")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

GPKG_PATH   = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\OSM\Data Proc\wue_final.gpkg"
OUTPUT_DIR  = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\OSM\Data Proc\data_check"
CLEAN_GPKG  = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\OSM\Data Proc\wue_poi_clean.gpkg"

# Spatial deduplication threshold in metres (same as preprocessing step)
SPATIAL_THRESHOLD_M = 50

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. LOAD
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 1 — Loading dataset")
print("=" * 60)

gdf = gpd.read_file(GPKG_PATH)

print(f"  CRS             : {gdf.crs}")
print(f"  Total features  : {len(gdf)}")
print(f"  Geometry types  : {gdf.geometry.geom_type.value_counts().to_dict()}")
print(f"  Columns         : {list(gdf.columns)}\n")

# ─────────────────────────────────────────────────────────────
# 2. MISSING VALUES
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 2 — Missing values")
print("=" * 60)

cols = ["osm_id", "code", "fclass", "name", "area_m2", "layer",
        "path", "source", "category", "gfa_m2", "type", "attraction_weight"]

# Only check columns that exist
cols_present = [c for c in cols if c in gdf.columns]
missing = gdf[cols_present].isnull().sum()
missing_pct = (missing / len(gdf) * 100).round(2)

missing_df = pd.DataFrame({"missing_count": missing, "missing_%": missing_pct})
print(missing_df.to_string())

# Flag rows with no name
no_name = gdf["name"].isnull().sum() if "name" in gdf.columns else "N/A"
print(f"\n  Features without name : {no_name}")

# Flag rows with null geometry
null_geom = gdf.geometry.isnull().sum()
print(f"  Null geometries       : {null_geom}\n")

# ─────────────────────────────────────────────────────────────
# 3. DUPLICATE DETECTION
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 3 — Duplicate detection")
print("=" * 60)

# 3a. Exact osm_id duplicates
if "osm_id" in gdf.columns:
    dup_osmid = gdf[gdf.duplicated(subset=["osm_id"], keep=False)]
    print(f"  Exact osm_id duplicates       : {len(dup_osmid)}")
    if len(dup_osmid) > 0:
        print(dup_osmid[["osm_id", "fclass", "name", "source", "category"]].head(10).to_string())
        print()

# 3b. Exact geometry duplicates (WKT)
gdf["_wkt"] = gdf.geometry.to_wkt()
dup_geom = gdf[gdf.duplicated(subset=["_wkt"], keep=False)]
print(f"  Exact geometry duplicates     : {len(dup_geom)}")

# 3c. Same osm_id + fclass (cross-layer duplicates)
if "fclass" in gdf.columns and "osm_id" in gdf.columns:
    dup_combo = gdf[gdf.duplicated(subset=["osm_id", "fclass"], keep=False)]
    print(f"  osm_id + fclass duplicates    : {len(dup_combo)}")
    if len(dup_combo) > 0:
        print(dup_combo[["osm_id", "fclass", "name", "source", "category"]].head(10).to_string())

# 3d. Spatial proximity duplicates — same fclass within 50m
print(f"\n  Checking spatial proximity duplicates (< {SPATIAL_THRESHOLD_M}m, same fclass) ...")

gdf_proj = gdf.copy()
gdf_proj = gdf_proj[gdf_proj.geometry.notnull()].copy()

# Find pairs within threshold using spatial join
from shapely.geometry import Point
buffered = gdf_proj.copy()
buffered["geometry"] = gdf_proj.geometry.buffer(SPATIAL_THRESHOLD_M / 2)

joined = gpd.sjoin(gdf_proj[["osm_id", "fclass", "geometry"]].reset_index(),
                   buffered[["osm_id", "fclass", "geometry"]].reset_index(),
                   how="inner", predicate="within")

# Remove self-joins and keep only same fclass
spatial_dups = joined[
    (joined["index_left"] != joined["index_right"]) &
    (joined["fclass_left"] == joined["fclass_right"])
]
n_spatial_dups = len(spatial_dups) // 2  # pairs → divide by 2
print(f"  Spatial proximity duplicate pairs : {n_spatial_dups}\n")

# ─────────────────────────────────────────────────────────────
# 4. CATEGORY & SOURCE DISTRIBUTION
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 4 — Category & source distribution")
print("=" * 60)

if "category" in gdf.columns:
    cat_dist = gdf["category"].value_counts()
    print("\n  Category distribution:")
    print(cat_dist.to_string())

if "source" in gdf.columns:
    src_dist = gdf["source"].value_counts()
    print("\n  Source distribution:")
    print(src_dist.to_string())

if "fclass" in gdf.columns:
    fclass_dist = gdf["fclass"].value_counts()
    print(f"\n  Unique fclass values : {gdf['fclass'].nunique()}")
    print("  Top 20 fclass counts:")
    print(fclass_dist.head(20).to_string())

print()

# ─────────────────────────────────────────────────────────────
# 5. NUMERICAL OUTLIER CHECK
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 5 — Numerical outlier check")
print("=" * 60)

num_cols = [c for c in ["gfa_m2", "area_m2", "attraction_weight"] if c in gdf.columns]

for col in num_cols:
    series = gdf[col].dropna()
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    upper = q3 + 3 * iqr
    lower = q1 - 3 * iqr
    outliers = series[(series > upper) | (series < lower)]

    print(f"\n  {col}:")
    print(f"    count={len(series)}, min={series.min():.1f}, "
          f"max={series.max():.1f}, mean={series.mean():.1f}, "
          f"median={series.median():.1f}")
    print(f"    IQR outliers (3×IQR): {len(outliers)} rows")

    if len(outliers) > 0 and len(outliers) <= 20:
        idx_out = outliers.index
        print(gdf.loc[idx_out, ["osm_id", "fclass", "name", "category", col]].to_string())

# Plot distributions
fig, axes = plt.subplots(1, len(num_cols), figsize=(5 * len(num_cols), 4))
if len(num_cols) == 1:
    axes = [axes]

for ax, col in zip(axes, num_cols):
    vals = gdf[col].dropna()
    ax.hist(vals, bins=60, color="#1a3a5c", edgecolor="white", linewidth=0.3)
    ax.set_title(col, fontsize=11)
    ax.set_xlabel("Value", fontsize=9)
    ax.set_ylabel("Count", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color="#dddddd", linewidth=0.6, linestyle="--")

plt.suptitle("Distribution of Numerical Attributes — wue_poi_final", fontsize=12, y=1.02)
plt.tight_layout()
dist_path = os.path.join(OUTPUT_DIR, "attribute_distributions.png")
plt.savefig(dist_path, dpi=300, bbox_inches="tight")
plt.show()
print(f"\n  Distribution plot saved: {dist_path}\n")

# ─────────────────────────────────────────────────────────────
# 6. REMOVE DUPLICATES & SAVE CLEAN FILE
# ─────────────────────────────────────────────────────────────

print("=" * 60)
print("  STEP 6 — Remove duplicates & save")
print("=" * 60)

n_before = len(gdf)

# Drop internal helper column
gdf_clean = gdf.drop(columns=["_wkt"], errors="ignore").copy()

# a) Remove exact geometry duplicates (keep first)
gdf_clean["_wkt"] = gdf_clean.geometry.to_wkt()
gdf_clean = gdf_clean.drop_duplicates(subset=["_wkt"], keep="first")
print(f"  After removing exact geometry duplicates : {len(gdf_clean)}")

# b) Remove exact osm_id + fclass duplicates (keep first = prefer POI point layer)
if "osm_id" in gdf_clean.columns and "fclass" in gdf_clean.columns:
    gdf_clean = gdf_clean.drop_duplicates(subset=["osm_id", "fclass"], keep="first")
    print(f"  After removing osm_id+fclass duplicates : {len(gdf_clean)}")

# c) Drop rows with null geometry
gdf_clean = gdf_clean[gdf_clean.geometry.notnull()]
print(f"  After dropping null geometries          : {len(gdf_clean)}")

# Clean up helper column
gdf_clean = gdf_clean.drop(columns=["_wkt"], errors="ignore")

n_after = len(gdf_clean)
n_removed = n_before - n_after

print(f"\n  ─────────────────────────────────────────")
print(f"  Features before : {n_before}")
print(f"  Features after  : {n_after}")
print(f"  Removed         : {n_removed}")
print(f"  ─────────────────────────────────────────\n")

# Save
gdf_clean.to_file(CLEAN_GPKG, driver="GPKG")
print(f"  Clean file saved: {CLEAN_GPKG}")
print()

# Final summary by category
if "category" in gdf_clean.columns:
    print("  Final category distribution (clean dataset):")
    print(gdf_clean["category"].value_counts().to_string())

print("\n  ✓ Data quality check complete.\n")
print(f"  Use '{os.path.basename(CLEAN_GPKG)}' for all clustering steps.")