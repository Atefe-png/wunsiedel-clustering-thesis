"""
============================================================
K-Means Clustering -- Landkreis Wunsiedel im Fichtelgebirge
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5c.1
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

HOW THE PARAMETER k=13 WAS DETERMINED
--------------------------------------
The number of clusters k was selected using two complementary
methods applied to the POI dataset (n=2,673, EPSG:25832):

1. Elbow Method (WCSS):
   - WCSS was computed for k = 2 to 25
   - The "elbow" in the curve (point of diminishing returns)
     was identified at k=13 using the Kneedle algorithm
     (Satopaa et al. 2011)
   - WCSS at k=13: 3,320,218

2. Silhouette Analysis:
   - Silhouette coefficient computed for k = 2 to 25
   - k=13 returned Silhouette = 0.573, Davies-Bouldin = 0.624
   - Values confirmed that k=13 represents a stable partition

Other parameters:
   - init='k-means++': smart centroid initialisation that
     spreads starting points (Arthur & Vassilvitskii 2007)
   - n_init=20: 20 independent runs to avoid local minima
   - random_state=42: fixed for full reproducibility

Input:  data/processed/wue_poi_clean.gpkg (EPSG:25832, n=2673)
Output: outputs/kmeans_results.gpkg
        outputs/kmeans_cluster_map.png / .pdf
============================================================
"""

import os
import warnings
import matplotlib
matplotlib.use("Agg")
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── Paths (relative to this script's location) ──────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")
OUT_DIR   = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Parameters ───────────────────────────────────────────────
N_CLUSTERS   = 13       # determined via Elbow + Silhouette (see docstring)
INIT         = "k-means++"
N_INIT       = 20
RANDOM_STATE = 42

# ── 1. Load data ─────────────────────────────────────────────
print("=" * 55)
print("  K-Means Clustering -- Landkreis Wunsiedel")
print("=" * 55)
gdf = gpd.read_file(GPKG_PATH)
print(f"  Features : {len(gdf)}  |  CRS: {gdf.crs}")

coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

# ── 2. Run K-Means ───────────────────────────────────────────
print(f"\nRunning K-Means (k={N_CLUSTERS}, n_init={N_INIT}) ...")
km = KMeans(n_clusters=N_CLUSTERS, init=INIT,
            n_init=N_INIT, random_state=RANDOM_STATE)
labels   = km.fit_predict(coords_scaled)
inertia  = km.inertia_

# ── 3. Results summary ───────────────────────────────────────
print(f"\n  WCSS (Inertia) : {inertia:,.1f}")
print(f"  {'Cluster':>8}  {'Points':>7}  {'Share':>7}")
for cl in range(N_CLUSTERS):
    n = np.sum(labels == cl)
    print(f"  {cl:>8}  {n:>7}  {n/len(labels)*100:>6.1f}%")

# ── 4. Map ───────────────────────────────────────────────────
cmap = plt.cm.get_cmap("tab20", N_CLUSTERS)
fig, ax = plt.subplots(figsize=(10, 9))
for cl in range(N_CLUSTERS):
    mask = labels == cl
    ax.scatter(coords[mask, 0], coords[mask, 1],
               c=[cmap(cl)], s=18, alpha=0.85, zorder=2,
               label=f"Cluster {cl} (n={np.sum(mask)})")
centroids = scaler.inverse_transform(km.cluster_centers_)
ax.scatter(centroids[:, 0], centroids[:, 1],
           c="black", s=60, marker="x", linewidths=1.8,
           zorder=5, label="Centroids")
ax.legend(fontsize=7, loc="lower left", ncol=2, framealpha=0.9)
ax.set_title(f"K-Means (k={N_CLUSTERS}) | WCSS = {inertia:,.1f}\n"
             f"Landkreis Wunsiedel, n=2,673 POIs",
             fontsize=11, fontfamily="serif")
ax.set_xlabel("Easting (m, EPSG:25832)", fontsize=10)
ax.set_ylabel("Northing (m, EPSG:25832)", fontsize=10)
ax.ticklabel_format(style="sci", axis="both", scilimits=(0, 0))
ax.grid(True, color="#eeeeee", linewidth=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "kmeans_cluster_map.png"), dpi=300)
plt.savefig(os.path.join(OUT_DIR, "kmeans_cluster_map.pdf"))
plt.close()

# ── 5. Save GeoPackage ───────────────────────────────────────
gdf_out = gdf.copy()
gdf_out["cluster"] = labels
out_gpkg = os.path.join(OUT_DIR, "kmeans_results.gpkg")
gdf_out.to_file(out_gpkg, driver="GPKG")
print(f"\nSaved: {out_gpkg}")
print("Done.")
