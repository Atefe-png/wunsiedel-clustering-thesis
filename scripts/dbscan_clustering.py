"""
============================================================
DBSCAN Clustering -- Landkreis Wunsiedel im Fichtelgebirge
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5c.2
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

HOW THE PARAMETERS eps=515m, MinPts=5 WERE DETERMINED
------------------------------------------------------
DBSCAN requires two parameters: eps (neighbourhood radius)
and MinPts (minimum points to form a dense region).

Step 1 — MinPts:
   MinPts = 5 is the standard recommendation for 2D spatial
   data (Ester et al. 1996). It was kept fixed across all runs.

Step 2 — eps via k-distance graph:
   - For each point, the distance to its 5th nearest neighbour
     was computed (k = MinPts = 5)
   - These distances were sorted and plotted (k-dist graph)
   - The "elbow" in the curve indicates the natural density
     threshold; visually identified at approximately 515 metres
   - This means: points closer than 515m to at least 4 others
     are considered core points

Step 3 — Sensitivity analysis (three runs):
   Run 1: eps=412m (-20%)  →  more clusters, more noise
   Run 2: eps=515m (primary, selected)
   Run 3: eps=618m (+20%)  →  fewer clusters, less noise
   Run 2 was selected as primary because it produced the
   best balance: meaningful spatial zones, moderate noise (13%)

Note on coordinate space:
   DBSCAN is applied directly in EPSG:25832 (metres), so eps
   is expressed in real-world metres — no standardisation needed.

Input:  data/processed/wue_poi_clean.gpkg (EPSG:25832, n=2673)
Output: outputs/dbscan_run2_results.gpkg  (primary)
        outputs/dbscan_run{1,2,3}_cluster_map.png
============================================================
"""

import os
import warnings
import matplotlib
matplotlib.use("Agg")
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")
OUT_DIR   = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Parameters ───────────────────────────────────────────────
MINPTS = 5   # standard for 2D spatial data (Ester et al. 1996)
RUNS = [
    {"run": 1, "eps_m": 412, "label": "eps=412m (-20%)"},
    {"run": 2, "eps_m": 515, "label": "eps=515m (primary, from k-dist graph)"},
    {"run": 3, "eps_m": 618, "label": "eps=618m (+20%)"},
]

# ── 1. Load data ─────────────────────────────────────────────
print("=" * 60)
print("  DBSCAN Clustering -- Landkreis Wunsiedel")
print("=" * 60)
gdf = gpd.read_file(GPKG_PATH)
print(f"  Features : {len(gdf)}  |  CRS: {gdf.crs}")
coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])

# ── 2. Three sensitivity runs ─────────────────────────────────
for cfg in RUNS:
    run_n, eps_m = cfg["run"], cfg["eps_m"]
    print(f"\nRun {run_n}: eps={eps_m}m, MinPts={MINPTS}")

    db = DBSCAN(eps=eps_m, min_samples=MINPTS,
                metric="euclidean", n_jobs=-1)
    labels = db.fit_predict(coords)

    n_cl    = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = int(np.sum(labels == -1))
    pct     = n_noise / len(labels) * 100

    print(f"  Clusters : {n_cl}  |  Noise: {n_noise} ({pct:.1f}%)")

    # Map
    unique_cl  = sorted([c for c in set(labels) if c != -1])
    cmap       = plt.cm.get_cmap("tab20", max(len(unique_cl), 1))
    fig, ax    = plt.subplots(figsize=(10, 9))
    noise_mask = labels == -1
    ax.scatter(coords[noise_mask, 0], coords[noise_mask, 1],
               c="lightgrey", s=8, alpha=0.4, zorder=1,
               label=f"Noise (n={n_noise})")
    for cl in unique_cl:
        mask = labels == cl
        ax.scatter(coords[mask, 0], coords[mask, 1],
                   c=[cmap(unique_cl.index(cl))], s=18,
                   alpha=0.85, zorder=2,
                   label=f"Cluster {cl} (n={int(np.sum(mask))})")
    ax.set_title(
        f"DBSCAN | eps={eps_m}m, MinPts={MINPTS} | "
        f"{n_cl} clusters, {pct:.1f}% noise\n"
        f"Landkreis Wunsiedel, n=2,673 POIs",
        fontsize=11, fontfamily="serif")
    ax.set_xlabel("Easting (m, EPSG:25832)", fontsize=10)
    ax.set_ylabel("Northing (m, EPSG:25832)", fontsize=10)
    ax.ticklabel_format(style="sci", axis="both", scilimits=(0, 0))
    ax.legend(fontsize=6, loc="lower left", ncol=2, framealpha=0.9)
    ax.grid(True, color="#eeeeee", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, f"dbscan_run{run_n}_cluster_map.png"), dpi=300)
    plt.savefig(os.path.join(OUT_DIR, f"dbscan_run{run_n}_cluster_map.pdf"))
    plt.close()

    # GeoPackage
    gdf_out = gdf.copy()
    gdf_out["cluster"] = labels
    gpkg = os.path.join(OUT_DIR, f"dbscan_run{run_n}_results.gpkg")
    gdf_out.to_file(gpkg, driver="GPKG")
    print(f"  Saved: {gpkg}")

print("\nDone. Primary result: outputs/dbscan_run2_results.gpkg")
