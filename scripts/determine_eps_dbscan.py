"""
============================================================
DBSCAN Parameter Selection — Sorted k-dist Graph
------------------------------------------------------------
Thesis Section 5c — Parameter Selection for DBSCAN
Based on: Ester et al. (1996), KDD-96

This script computes the sorted 4-dist graph as proposed in
the original DBSCAN paper and helps visually identify the
elbow point that determines the optimal Eps value.

Input:  wue_poi_clean.gpkg (EPSG:25832, units: metres)
Output: - kdist_graph.png / .pdf  (for thesis figure)
        - console output with suggested Eps values
============================================================
"""

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator
import os
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────

GPKG_PATH  = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\OSM\Data Proc\wue_poi_clean.gpkg"
OUTPUT_DIR = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\cluster_analysis"

K          = 4        # As recommended by Ester et al. (1996) for 2D data
MINPTS     = 5        # MinPts used in the actual DBSCAN run

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. LOAD & EXTRACT COORDINATES
# ─────────────────────────────────────────────────────────────

print("Loading data ...")
gdf = gpd.read_file(GPKG_PATH)
print(f"  Features loaded : {len(gdf)}")
print(f"  CRS             : {gdf.crs}  (unit: metres)\n")

coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])

# ─────────────────────────────────────────────────────────────
# 2. COMPUTE k-dist (distance to k-th nearest neighbour)
# ─────────────────────────────────────────────────────────────

print(f"Computing {K}-dist for each point ...")
nbrs = NearestNeighbors(n_neighbors=K + 1, algorithm="ball_tree", metric="euclidean")
nbrs.fit(coords)
distances, _ = nbrs.kneighbors(coords)

# Distance to k-th nearest neighbour (index K, since index 0 = self)
kdist = np.sort(distances[:, K])[::-1]   # descending order

print(f"  k-dist range: {kdist.min():.1f} m  –  {kdist.max():.1f} m")
print(f"  Median k-dist: {np.median(kdist):.1f} m\n")

# ─────────────────────────────────────────────────────────────
# 3. DETECT ELBOW (Kneedle algorithm)
# ─────────────────────────────────────────────────────────────

x_vals = np.arange(len(kdist))

try:
    kneedle = KneeLocator(
        x_vals, kdist,
        curve="convex",
        direction="decreasing",
        interp_method="polynomial"
    )
    knee_idx = kneedle.knee
    eps_suggested = kdist[knee_idx] if knee_idx is not None else None
except Exception:
    knee_idx = None
    eps_suggested = None

# ─────────────────────────────────────────────────────────────
# 4. PLOT
# ─────────────────────────────────────────────────────────────

fig, ax = plt.subplots(figsize=(9, 4.5))

ax.plot(x_vals, kdist, color="#1a3a5c", linewidth=1.5, label=f"Sorted {K}-dist")

if knee_idx is not None and eps_suggested is not None:
    ax.axhline(eps_suggested, color="#c0392b", linewidth=1.4,
               linestyle="--", label=f"Suggested $\\varepsilon$ = {eps_suggested:.0f} m")
    ax.axvline(knee_idx, color="#c0392b", linewidth=0.8, linestyle=":")
    ax.scatter([knee_idx], [eps_suggested], color="#c0392b", zorder=5, s=60)

    # Also show ±20% sensitivity range
    eps_low  = eps_suggested * 0.80
    eps_high = eps_suggested * 1.20
    ax.axhline(eps_low,  color="#e67e22", linewidth=1.0, linestyle=":",
               label=f"$\\varepsilon -20\\%$ = {eps_low:.0f} m")
    ax.axhline(eps_high, color="#e67e22", linewidth=1.0, linestyle="-.",
               label=f"$\\varepsilon +20\\%$ = {eps_high:.0f} m")

ax.set_xlabel("Points sorted by decreasing distance", fontsize=11, fontfamily="serif")
ax.set_ylabel(f"Distance to {K}-th nearest neighbour (m)", fontsize=11, fontfamily="serif")
ax.set_title(f"Sorted {K}-dist Graph for DBSCAN $\\varepsilon$ Selection\n"
             f"Landkreis Wunsiedel POI Dataset ($n = {len(gdf):,}$)",
             fontsize=12, fontfamily="serif")
ax.legend(fontsize=9)
ax.grid(True, color="#dddddd", linewidth=0.6, linestyle="--")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

plt.tight_layout()

out_png = os.path.join(OUTPUT_DIR, "dbscan_kdist_graph.png")
out_pdf = os.path.join(OUTPUT_DIR, "dbscan_kdist_graph.pdf")
plt.savefig(out_png, dpi=300, bbox_inches="tight")
plt.savefig(out_pdf, bbox_inches="tight")
plt.show()

# ─────────────────────────────────────────────────────────────
# 5. SUMMARY
# ─────────────────────────────────────────────────────────────

print("=" * 55)
print("  DBSCAN PARAMETER RECOMMENDATION")
print("=" * 55)
print(f"  MinPts          : {MINPTS}  (fixed, 2D spatial data)")
print(f"  k used for dist : {K}  (Ester et al. 1996)")

if eps_suggested is not None:
    print(f"\n  Suggested Eps   : {eps_suggested:.1f} m  (elbow/knee point)")
    print(f"  Sensitivity low : {eps_suggested * 0.80:.1f} m  (-20%)")
    print(f"  Sensitivity high: {eps_suggested * 1.20:.1f} m  (+20%)")
    print()
    print("  → Use these three values as runs 1, 2, 3 in Table 5.x")
    print("    of your thesis (Section 5c, DBSCAN parameter table).")
else:
    print("\n  ⚠ No clear elbow detected automatically.")
    print("    Please inspect the plot and choose Eps manually")
    print("    at the first visible change in gradient.")

print()
print(f"  Plots saved to: {OUTPUT_DIR}")
print("=" * 55)
