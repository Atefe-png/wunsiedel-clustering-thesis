"""
============================================================
Data Cleaning & Deduplication — OSM POI Dataset
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 4.3
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

This script processes the raw OSM GeoPackage (wue_final.gpkg)
and produces the cleaned dataset (wue_poi_clean.gpkg, n=2,673)
used in all clustering steps.

WHAT THIS SCRIPT DOES (step by step):
--------------------------------------
1. Loads wue_final.gpkg — the merged POI dataset from OSM
   (points + polygon centroids, Landkreis Wunsiedel)

2. Removes exact geometry duplicates (same WKT coordinates)

3. Removes cross-layer duplicates (same osm_id + fclass,
   e.g. a shop appearing in both the POI point layer and
   the building polygon layer — keep the point)

4. Drops features with null geometry

5. Saves the cleaned result as wue_poi_clean.gpkg

Result: 2,673 features, EPSG:25832 (UTM Zone 32N, metres)

Input:  data/raw/wue_final.gpkg
Output: data/processed/wue_poi_clean.gpkg
============================================================
"""

import os
import warnings
import geopandas as gpd

warnings.filterwarnings("ignore")

# ── Paths (relative to this script) ─────────────────────────
ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_GPKG = os.path.join(ROOT, "data", "raw", "wue_final.gpkg")
CLEAN_GPKG = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")

os.makedirs(os.path.dirname(CLEAN_GPKG), exist_ok=True)

# ── 1. Load ──────────────────────────────────────────────────
print("Loading raw dataset ...")
gdf = gpd.read_file(INPUT_GPKG)
print(f"  Features loaded : {len(gdf)}")
print(f"  CRS             : {gdf.crs}")
print(f"  Columns         : {list(gdf.columns)}")

n_before = len(gdf)

# ── 2. Remove exact geometry duplicates ──────────────────────
gdf["_wkt"] = gdf.geometry.to_wkt()
gdf = gdf.drop_duplicates(subset=["_wkt"], keep="first")
print(f"\nAfter exact geometry deduplication : {len(gdf)}")

# ── 3. Remove cross-layer duplicates (osm_id + fclass) ───────
if "osm_id" in gdf.columns and "fclass" in gdf.columns:
    gdf = gdf.drop_duplicates(subset=["osm_id", "fclass"], keep="first")
    print(f"After osm_id + fclass deduplication: {len(gdf)}")

# ── 4. Drop null geometries ───────────────────────────────────
gdf = gdf[gdf.geometry.notnull()].copy()
gdf = gdf.drop(columns=["_wkt"], errors="ignore")
print(f"After dropping null geometries     : {len(gdf)}")

# ── 5. Summary & save ─────────────────────────────────────────
n_removed = n_before - len(gdf)
print(f"\nRemoved total : {n_removed} duplicates")
print(f"Final dataset : {len(gdf)} features")

gdf.to_file(CLEAN_GPKG, driver="GPKG")
print(f"\nSaved: {CLEAN_GPKG}")
print("Done. Use data/processed/wue_poi_clean.gpkg for all clustering steps.")
