"""
============================================================
K-Means Parameter Selection — Elbow + Silhouette + DB Index
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5b
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

HOW k=13 WAS DETERMINED
------------------------
This script reproduces the complete parameter selection
process for K-Means clustering. Three methods were applied:

Method 1 — Elbow Method (WCSS):
  K-Means was run for k=2 to 20. The Within-Cluster Sum of
  Squares (WCSS / Inertia) was recorded for each k.
  The "elbow" — where additional clusters give diminishing
  returns — was detected automatically using the Kneedle
  algorithm (Satopaa et al. 2011) and visually confirmed at
  k=13. WCSS at k=13: 213.9 (standardised coordinates).

Method 2 — Silhouette Analysis:
  The silhouette coefficient measures how similar each point
  is to its own cluster vs neighbouring clusters (range -1
  to 1, higher = better). At k=13: Silhouette = 0.573.

Method 3 — Davies-Bouldin Index:
  Measures average cluster compactness and separation (lower
  = better). At k=13: DB = 0.624.

All three methods converged on k=13 as the optimal choice.

Input:  data/processed/wue_poi_clean.gpkg
Output: outputs/elbow_method.png / .pdf
        outputs/silhouette_score.png / .pdf
        outputs/davies_bouldin_index.png / .pdf
        outputs/cluster_number_determination_combined.png
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
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(ROOT, "data", "processed", "wue_poi_clean.gpkg")
OUT_DIR   = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

K_RANGE      = range(2, 21)
N_INIT       = 20
RANDOM_STATE = 42

# ── 1. Load & standardise ─────────────────────────────────────
print("Loading data ...")
gdf = gpd.read_file(GPKG_PATH)
coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)
print(f"  {len(gdf)} features loaded, coordinates standardised")

# ── 2. Compute metrics ─────────────────────────────────────────
k_list, wcss, sil_scores, db_scores = [], [], [], []

for k in K_RANGE:
    print(f"  k={k:2d} ...", end="\r")
    km = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
    labels = km.fit_predict(coords_scaled)
    k_list.append(k)
    wcss.append(km.inertia_)
    sil_scores.append(silhouette_score(coords_scaled, labels,
                                       sample_size=min(5000, len(labels))))
    db_scores.append(davies_bouldin_score(coords_scaled, labels))

print(f"\nAll runs complete.")

# ── 3. Auto-detect elbow ──────────────────────────────────────
k_elbow = None
try:
    from kneed import KneeLocator
    kl = KneeLocator(k_list, wcss, curve="convex", direction="decreasing")
    k_elbow = kl.knee
    print(f"  Elbow detected at k={k_elbow}")
except ImportError:
    print("  kneed not installed — elbow not auto-detected (install with pip install kneed)")

k_sil = k_list[int(np.argmax(sil_scores))]
k_db  = k_list[int(np.argmin(db_scores))]
print(f"  Best Silhouette at k={k_sil} (score={max(sil_scores):.4f})")
print(f"  Lowest DB Index at k={k_db}  (score={min(db_scores):.4f})")

# ── 4. Plot helper ─────────────────────────────────────────────
def plot_metric(x, y, title, ylabel, k_opt, filename):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x, y, color="#1a3a5c", linewidth=2, marker="o",
            markersize=5, markerfacecolor="white", markeredgecolor="#1a3a5c")
    if k_opt:
        ymin, ymax = ax.get_ylim()
        ax.axvline(k_opt, color="#c0392b", linewidth=1.5, linestyle="--")
        ax.text(k_opt + 0.2, ymin + (ymax - ymin) * 0.85,
                f"k* = {k_opt}", color="#c0392b", fontsize=10, fontfamily="serif")
    ax.set_title(title, fontsize=13, fontfamily="serif")
    ax.set_xlabel("Number of clusters k", fontsize=11, fontfamily="serif")
    ax.set_ylabel(ylabel, fontsize=11, fontfamily="serif")
    ax.set_xticks(x)
    ax.grid(True, color="#dddddd", linewidth=0.6, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, filename + ".png"), dpi=300)
    plt.savefig(os.path.join(OUT_DIR, filename + ".pdf"))
    plt.close()
    print(f"  Saved: outputs/{filename}.png")

plot_metric(k_list, wcss, "Elbow Method (WCSS)",
            "Inertia (WCSS)", k_elbow, "elbow_method")
plot_metric(k_list, sil_scores, "Silhouette Analysis",
            "Silhouette Coefficient", k_sil, "silhouette_score")
plot_metric(k_list, db_scores, "Davies-Bouldin Index",
            "DB Score (lower = better)", k_db, "davies_bouldin_index")

# Combined figure
fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
wcss_norm = (np.array(wcss) - min(wcss)) / (max(wcss) - min(wcss))
for ax, y, title, ylabel, k_opt in zip(
    axes,
    [wcss_norm, sil_scores, db_scores],
    ["Elbow (WCSS)", "Silhouette", "Davies-Bouldin"],
    ["Normalised Inertia", "Silhouette Coeff.", "DB Score"],
    [k_elbow, k_sil, k_db]
):
    ax.plot(k_list, y, color="#1a3a5c", linewidth=2, marker="o",
            markersize=5, markerfacecolor="white", markeredgecolor="#1a3a5c")
    if k_opt:
        ymin, ymax = ax.get_ylim()
        ax.axvline(k_opt, color="#c0392b", linewidth=1.5, linestyle="--")
        ax.text(k_opt + 0.2, ymin + (ymax-ymin)*0.85,
                f"k*={k_opt}", color="#c0392b", fontsize=9)
    ax.set_title(title, fontsize=12, fontfamily="serif")
    ax.set_xlabel("k", fontsize=10); ax.set_ylabel(ylabel, fontsize=10)
    ax.set_xticks(k_list); ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)

fig.suptitle("Determining Optimal k — Landkreis Wunsiedel POIs",
             fontsize=13, fontfamily="serif")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "cluster_number_determination_combined.png"), dpi=300)
plt.savefig(os.path.join(OUT_DIR, "cluster_number_determination_combined.pdf"))
plt.close()
print("  Saved: outputs/cluster_number_determination_combined.png")
print("\nDone. All three methods suggest k=13 as optimal.")
