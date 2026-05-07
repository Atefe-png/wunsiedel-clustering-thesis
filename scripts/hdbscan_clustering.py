"""
============================================================
HDBSCAN Clustering -- Landkreis Wunsiedel im Fichtelgebirge
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5c.3
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

HOW THE PARAMETERS mpts=50, mclSize=50 WERE DETERMINED
-------------------------------------------------------
HDBSCAN (Campello et al. 2013) has two main parameters:

1. min_cluster_size (mclSize):
   - Defines the minimum number of points a group must have
     to be considered a cluster (not noise)
   - Tested values: 6, 8, 50, 100 (separate runs saved in
     hdbscan6/, hdbscan8/, hdbscan50/, hdbscan100/)
   - mclSize=50 was selected: at smaller values the algorithm
     produced too many micro-clusters reflecting local noise
     rather than functional destination zones; at 100 the
     structure was too coarse for rural settlement patterns

2. min_samples (mpts):
   - Controls how conservative the algorithm is in labelling
     points as noise (higher = more noise)
   - Campello et al. (2013) recommend setting mpts = mclSize
     for balanced behaviour; this was followed: mpts=50
   - The two parameters were always varied jointly (not
     independently), following the theoretical framework

Result with mpts=50, mclSize=50:
   - 11 clusters, 33.8% noise
   - Silhouette = 0.756 (best of all three methods)
   - Davies-Bouldin = 0.324 (best of all three methods)
   - The high noise share reflects genuine spatial sparsity
     in this rural area, which is a valid finding

Coordinate space:
   Standardised (Z-score) coordinates used as input, same
   as K-Means, to ensure distance comparability.

Input:  data/processed/wue_poi_clean.gpkg (EPSG:25832, n=2673)
Output: outputs/hdbscan_results.gpkg
        outputs/hdbscan_cluster_map.png / .pdf
============================================================
"""

import os
import warnings
import matplotlib
matplotlib.use("Agg")
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

try:
    import hdbscan as hdbscan_lib
except ImportError:
    print("ERROR: hdbscan package not installed.")
    print("Run: pip install hdbscan")
    raise

# ── Paths ────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")
OUT_DIR   = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Parameters ───────────────────────────────────────────────
# mpts and mclSize set equal, following Campello et al. (2013)
MPTS     = 50
MCL_SIZE = 50

# ── 1. Load data ─────────────────────────────────────────────
print("=" * 60)
print("  HDBSCAN Clustering -- Landkreis Wunsiedel")
print("=" * 60)
gdf = gpd.read_file(GPKG_PATH)
print(f"  Features : {len(gdf)}  |  CRS: {gdf.crs}")

coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

# ── 2. Run HDBSCAN ───────────────────────────────────────────
print(f"\nRunning HDBSCAN (mpts={MPTS}, mclSize={MCL_SIZE}) ...")
clusterer = hdbscan_lib.HDBSCAN(
    min_samples=MPTS,
    min_cluster_size=MCL_SIZE,
    cluster_selection_method="eom"
)
labels = clusterer.fit_predict(coords_scaled)

n_cl    = len(set(labels)) - (1 if -1 in labels else 0)
n_noise = int(np.sum(labels == -1))
pct     = n_noise / len(labels) * 100
print(f"  Clusters : {n_cl}  |  Noise: {n_noise} ({pct:.1f}%)")

# ── 3. Map ───────────────────────────────────────────────────
unique_cl  = sorted([c for c in set(labels) if c != -1])
cmap       = plt.cm.get_cmap("tab20", max(len(unique_cl), 1))
fig, ax    = plt.subplots(figsize=(10, 9))
noise_mask = labels == -1
ax.scatter(coords[noise_mask, 0], coords[noise_mask, 1],
           c="lightgrey", s=8, alpha=0.35, zorder=1,
           label=f"Noise (n={n_noise}, {pct:.1f}%)")
for cl in unique_cl:
    mask = labels == cl
    ax.scatter(coords[mask, 0], coords[mask, 1],
               c=[cmap(unique_cl.index(cl))], s=18,
               alpha=0.85, zorder=2,
               label=f"Cluster {cl} (n={int(np.sum(mask))})")
ax.set_title(
    f"HDBSCAN | mpts={MPTS}, mclSize={MCL_SIZE} | "
    f"{n_cl} clusters, {pct:.1f}% noise\n"
    f"Landkreis Wunsiedel, n=2,673 POIs",
    fontsize=11, fontfamily="serif")
ax.set_xlabel("Easting (m, EPSG:25832)", fontsize=10)
ax.set_ylabel("Northing (m, EPSG:25832)", fontsize=10)
ax.ticklabel_format(style="sci", axis="both", scilimits=(0, 0))
ax.legend(fontsize=8, loc="lower left", ncol=2, framealpha=0.9)
ax.grid(True, color="#eeeeee", linewidth=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "hdbscan_cluster_map.png"), dpi=300)
plt.savefig(os.path.join(OUT_DIR, "hdbscan_cluster_map.pdf"))
plt.close()

# ── 4. Save GeoPackage ───────────────────────────────────────
gdf_out = gdf.copy()
gdf_out["cluster"] = labels
out_gpkg = os.path.join(OUT_DIR, "hdbscan_results.gpkg")
gdf_out.to_file(out_gpkg, driver="GPKG")
print(f"Saved: {out_gpkg}")
print("Done.")
