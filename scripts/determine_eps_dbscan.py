"""
============================================================
DBSCAN Parameter Selection — k-distance Graph
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5c.2
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

HOW ε=515m WAS DETERMINED
--------------------------
DBSCAN needs eps (ε) — the neighbourhood search radius in
metres — and MinPts. This script reproduces the full
parameter selection process.

Step 1 — MinPts = 5 (fixed):
  MinPts=5 is the standard recommendation for 2D spatial
  point data (Ester et al. 1996). It was not tuned further.

Step 2 — ε via k-distance graph:
  For each of the 2,673 POIs, the distance to its k-th
  nearest neighbour (k = MinPts - 1 = 4) was computed.
  These distances were sorted in descending order and plotted.
  The "elbow" in this curve marks the natural density
  threshold between dense regions (clusters) and sparse
  regions (noise). The elbow was detected automatically
  using the Kneedle algorithm and confirmed visually at
  approximately 515 metres.

Step 3 — Sensitivity analysis:
  Three runs were executed: ε = 412m (-20%), 515m (primary),
  618m (+20%). Run 2 (515m) was selected because it produced
  the best spatial coherence for rural Wunsiedel.

Important: DBSCAN is applied in raw EPSG:25832 metres,
NOT standardised coordinates. This means ε is directly
interpretable as a real-world distance.

Input:  data/processed/wue_poi_clean.gpkg
Output: outputs/dbscan_kdist_graph.png / .pdf
        console: suggested ε with ±20% range
============================================================
"""

import os
import warnings
import matplotlib
matplotlib.use("Agg")
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")
OUT_DIR   = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

K      = 4       # k for k-dist (= MinPts - 1, per Ester et al. 1996)
MINPTS = 5

# ── 1. Load data (raw metres, no standardisation) ─────────────
print("Loading data ...")
gdf = gpd.read_file(GPKG_PATH)
coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
print(f"  {len(gdf)} features | CRS: {gdf.crs} (metres)")

# ── 2. Compute k-distances ────────────────────────────────────
print(f"\nComputing {K}-dist for each point ...")
nbrs = NearestNeighbors(n_neighbors=K + 1, algorithm="ball_tree",
                        metric="euclidean")
nbrs.fit(coords)
distances, _ = nbrs.kneighbors(coords)
kdist = np.sort(distances[:, K])[::-1]   # descending
print(f"  k-dist range: {kdist.min():.1f} m — {kdist.max():.1f} m")
print(f"  Median k-dist: {np.median(kdist):.1f} m")

# ── 3. Auto-detect elbow ──────────────────────────────────────
x_vals = np.arange(len(kdist))
eps_suggested = None
knee_idx = None
try:
    from kneed import KneeLocator
    kl = KneeLocator(x_vals, kdist, curve="convex",
                     direction="decreasing", interp_method="polynomial")
    knee_idx = kl.knee
    eps_suggested = kdist[knee_idx] if knee_idx is not None else None
    print(f"\n  Elbow detected at index {knee_idx}")
    print(f"  Suggested eps = {eps_suggested:.1f} m")
except ImportError:
    print("\n  kneed not installed — install with: pip install kneed")
    print("  Inspect the plot manually and read eps from the elbow.")

# ── 4. Plot ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(x_vals, kdist, color="#1a3a5c", linewidth=1.5,
        label=f"Sorted {K}-dist (distance to {K}th neighbour)")

if eps_suggested is not None:
    eps_low  = eps_suggested * 0.80
    eps_high = eps_suggested * 1.20
    ax.axhline(eps_suggested, color="#c0392b", linewidth=1.5,
               linestyle="--",
               label=f"Suggested ε = {eps_suggested:.0f} m (elbow)")
    ax.axhline(eps_low,  color="#e67e22", linewidth=1.0,
               linestyle=":", label=f"ε −20% = {eps_low:.0f} m")
    ax.axhline(eps_high, color="#e67e22", linewidth=1.0,
               linestyle="-.", label=f"ε +20% = {eps_high:.0f} m")
    if knee_idx is not None:
        ax.scatter([knee_idx], [eps_suggested],
                   color="#c0392b", zorder=5, s=60)

ax.set_xlabel("Points sorted by decreasing k-dist", fontsize=11,
              fontfamily="serif")
ax.set_ylabel(f"Distance to {K}th nearest neighbour (m)", fontsize=11,
              fontfamily="serif")
ax.set_title(f"Sorted {K}-dist Graph for DBSCAN ε Selection\n"
             f"Landkreis Wunsiedel POI Dataset (n={len(gdf):,})",
             fontsize=12, fontfamily="serif")
ax.legend(fontsize=9)
ax.grid(True, color="#dddddd", linewidth=0.6, linestyle="--")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "dbscan_kdist_graph.png"), dpi=300)
plt.savefig(os.path.join(OUT_DIR, "dbscan_kdist_graph.pdf"))
plt.close()

# ── 5. Summary ────────────────────────────────────────────────
print("\n" + "=" * 50)
print("  DBSCAN PARAMETER RECOMMENDATION")
print("=" * 50)
print(f"  MinPts (fixed)   : {MINPTS}  (Ester et al. 1996)")
if eps_suggested is not None:
    print(f"  Suggested eps    : {eps_suggested:.1f} m")
    print(f"  Sensitivity low  : {eps_suggested*0.80:.1f} m (-20%)")
    print(f"  Sensitivity high : {eps_suggested*1.20:.1f} m (+20%)")
    print()
    print("  Run dbscan_clustering.py with all three values.")
    print("  Primary result: Run 2 (eps=515m) — see thesis Section 5c.2")
print(f"\nSaved: outputs/dbscan_kdist_graph.png")
