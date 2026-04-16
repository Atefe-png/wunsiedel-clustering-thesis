"""
============================================================
Determining the Optimal Number of Clusters for K-Means
------------------------------------------------------------
Thesis: Clustering Methods for POI Aggregation in Rural Areas
Case Study: Landkreis Wunsiedel im Fichtelgebirge
Section 5b — Anzahl der Cluster bestimmen

Methods used:
  1. Elbow Method (Within-Cluster Sum of Squares / Inertia)
  2. Silhouette Analysis
  3. Davies-Bouldin Index

Input:  wue_poi_final.gpkg  (EPSG:25832)
Output: Three diagnostic plots saved as publication-quality PDFs/PNGs
============================================================
"""

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
import warnings
import os

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# 0. CONFIGURATION — adjust paths as needed
# ─────────────────────────────────────────────────────────────

GPKG_PATH = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\OSM\Data Proc\wue_poi_clean.gpkg"
OUTPUT_DIR = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\cluster_analysis"
K_RANGE    = range(2, 21)          # k from 2 to 20
N_INIT     = 20                    # k-means restarts (higher = more stable)
RANDOM_STATE = 42
FIGSIZE    = (8, 4.5)

# Thesis plot style
FONT_FAMILY   = "serif"
TITLE_SIZE    = 13
LABEL_SIZE    = 11
TICK_SIZE     = 9
LINE_COLOR    = "#1a3a5c"
MARKER_COLOR  = "#c0392b"
GRID_COLOR    = "#dddddd"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────────────────────

print("Loading data ...")
gdf = gpd.read_file(GPKG_PATH)
print(f"  Total features loaded: {len(gdf)}")

# Extract projected coordinates (EPSG:25832 — metres)
coords = np.column_stack([gdf.geometry.x, gdf.geometry.y])

# Standardise so that x and y contribute equally
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

print(f"  Coordinate array shape: {coords_scaled.shape}")
print(f"  k range: {min(K_RANGE)} – {max(K_RANGE)}\n")

# ─────────────────────────────────────────────────────────────
# 2. COMPUTE METRICS ACROSS k
# ─────────────────────────────────────────────────────────────

inertia_values   = []
silhouette_values = []
db_values        = []

k_list = list(K_RANGE)

for k in k_list:
    print(f"  Running k-means for k = {k:2d} ...", end="\r")
    km = KMeans(n_clusters=k, n_init=N_INIT, random_state=RANDOM_STATE)
    labels = km.fit_predict(coords_scaled)

    inertia_values.append(km.inertia_)
    silhouette_values.append(silhouette_score(coords_scaled, labels, sample_size=min(5000, len(labels))))
    db_values.append(davies_bouldin_score(coords_scaled, labels))

print("\nAll k-means runs complete.\n")

# ─────────────────────────────────────────────────────────────
# 3. HELPER: shared plot style
# ─────────────────────────────────────────────────────────────

def style_ax(ax, title, ylabel):
    ax.set_title(title, fontsize=TITLE_SIZE, fontfamily=FONT_FAMILY, pad=8)
    ax.set_xlabel("Number of clusters $k$", fontsize=LABEL_SIZE, fontfamily=FONT_FAMILY)
    ax.set_ylabel(ylabel, fontsize=LABEL_SIZE, fontfamily=FONT_FAMILY)
    ax.tick_params(labelsize=TICK_SIZE)
    ax.set_xticks(k_list)
    ax.grid(True, color=GRID_COLOR, linewidth=0.7, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def add_optimal_vline(ax, k_opt, label_y_frac=0.85):
    ymin, ymax = ax.get_ylim()
    ax.axvline(k_opt, color=MARKER_COLOR, linewidth=1.6, linestyle="--", zorder=3)
    ax.text(
        k_opt + 0.25,
        ymin + (ymax - ymin) * label_y_frac,
        f"$k^* = {k_opt}$",
        fontsize=TICK_SIZE + 1,
        color=MARKER_COLOR,
        fontfamily=FONT_FAMILY,
    )


# ─────────────────────────────────────────────────────────────
# 4a. ELBOW PLOT (WCSS / Inertia)
# ─────────────────────────────────────────────────────────────

# Automatically detect elbow using the "kneedle" algorithm
try:
    from kneed import KneeLocator
    kneedle = KneeLocator(k_list, inertia_values, curve="convex", direction="decreasing")
    k_elbow = kneedle.knee if kneedle.knee else None
except ImportError:
    k_elbow = None

fig, ax = plt.subplots(figsize=FIGSIZE)
ax.plot(k_list, inertia_values, color=LINE_COLOR, linewidth=2, marker="o",
        markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(ax, "Elbow Method — Within-Cluster Sum of Squares (WCSS)", "Inertia (WCSS)")

if k_elbow:
    add_optimal_vline(ax, k_elbow)
    print(f"  Elbow detected at k = {k_elbow}")

plt.tight_layout()
elbow_path = os.path.join(OUTPUT_DIR, "elbow_method.png")
plt.savefig(elbow_path, dpi=300, bbox_inches="tight")
plt.savefig(os.path.join(OUTPUT_DIR, "elbow_method.pdf"), bbox_inches="tight")
plt.show()
print(f"  Saved: {elbow_path}\n")

# ─────────────────────────────────────────────────────────────
# 4b. SILHOUETTE SCORE PLOT
# ─────────────────────────────────────────────────────────────

k_sil = k_list[int(np.argmax(silhouette_values))]
print(f"  Best Silhouette Score at k = {k_sil}  (score = {max(silhouette_values):.4f})")

fig, ax = plt.subplots(figsize=FIGSIZE)
ax.plot(k_list, silhouette_values, color=LINE_COLOR, linewidth=2, marker="o",
        markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(ax, "Silhouette Analysis", "Average Silhouette Coefficient")
add_optimal_vline(ax, k_sil)

plt.tight_layout()
sil_path = os.path.join(OUTPUT_DIR, "silhouette_score.png")
plt.savefig(sil_path, dpi=300, bbox_inches="tight")
plt.savefig(os.path.join(OUTPUT_DIR, "silhouette_score.pdf"), bbox_inches="tight")
plt.show()
print(f"  Saved: {sil_path}\n")

# ─────────────────────────────────────────────────────────────
# 4c. DAVIES-BOULDIN INDEX PLOT
# ─────────────────────────────────────────────────────────────

k_db = k_list[int(np.argmin(db_values))]
print(f"  Lowest Davies-Bouldin Index at k = {k_db}  (score = {min(db_values):.4f})")

fig, ax = plt.subplots(figsize=FIGSIZE)
ax.plot(k_list, db_values, color=LINE_COLOR, linewidth=2, marker="o",
        markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(ax, "Davies-Bouldin Index", "Davies-Bouldin Score (lower = better)")
add_optimal_vline(ax, k_db)

plt.tight_layout()
db_path = os.path.join(OUTPUT_DIR, "davies_bouldin_index.png")
plt.savefig(db_path, dpi=300, bbox_inches="tight")
plt.savefig(os.path.join(OUTPUT_DIR, "davies_bouldin_index.pdf"), bbox_inches="tight")
plt.show()
print(f"  Saved: {db_path}\n")

# ─────────────────────────────────────────────────────────────
# 5. COMBINED OVERVIEW PLOT (all 3 metrics in one figure)
# ─────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
fig.suptitle(
    "Determining the Optimal Number of Clusters — Landkreis Wunsiedel",
    fontsize=14, fontfamily=FONT_FAMILY, y=1.02
)

# Inertia (normalised 0–1 for comparability in combined plot)
inertia_norm = (np.array(inertia_values) - min(inertia_values)) / \
               (max(inertia_values) - min(inertia_values))

axes[0].plot(k_list, inertia_norm, color=LINE_COLOR, linewidth=2,
             marker="o", markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(axes[0], "Elbow Method (WCSS)", "Normalised Inertia")
if k_elbow:
    add_optimal_vline(axes[0], k_elbow)

axes[1].plot(k_list, silhouette_values, color=LINE_COLOR, linewidth=2,
             marker="o", markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(axes[1], "Silhouette Analysis", "Silhouette Coefficient")
add_optimal_vline(axes[1], k_sil)

axes[2].plot(k_list, db_values, color=LINE_COLOR, linewidth=2,
             marker="o", markersize=5, markerfacecolor="white", markeredgecolor=LINE_COLOR)
style_ax(axes[2], "Davies-Bouldin Index", "DB Score (lower = better)")
add_optimal_vline(axes[2], k_db)

plt.tight_layout()
combined_path = os.path.join(OUTPUT_DIR, "cluster_number_determination_combined.png")
plt.savefig(combined_path, dpi=300, bbox_inches="tight")
plt.savefig(os.path.join(OUTPUT_DIR, "cluster_number_determination_combined.pdf"), bbox_inches="tight")
plt.show()
print(f"  Saved combined plot: {combined_path}\n")

# ─────────────────────────────────────────────────────────────
# 6. SUMMARY TABLE
# ─────────────────────────────────────────────────────────────

print("=" * 55)
print("  SUMMARY — Optimal k by method")
print("=" * 55)
print(f"  Elbow Method (WCSS)      : k = {k_elbow if k_elbow else 'not detected'}")
print(f"  Silhouette Analysis      : k = {k_sil}  (score = {max(silhouette_values):.4f})")
print(f"  Davies-Bouldin Index     : k = {k_db}  (score = {min(db_values):.4f})")
print("=" * 55)
print()
print("All outputs saved to:")
print(f"  {OUTPUT_DIR}")
print()
print("Next step: use the agreed k value in Section 5c (k-means clustering).")
