"""
============================================================
Attraction Weight Aggregation — W_c = sum(w_i for i in c)
------------------------------------------------------------
Thesis Section 4.5 — Workflow: From POI Data to Destination Zones
Based on: Bosserhoff (2023), Klinkhardt et al. (2021)

For each clustering method, this script:
  1. Loads the GeoPackage with cluster labels
  2. Computes W_c = sum of attraction_weight per cluster
  3. Computes cluster centroid (geometric mean of members)
  4. Saves results as CSV and GeoPackage (zone centroids)
  5. Prints thesis-ready summary table

Input files:
  kmeans_results.gpkg      (cluster column: 'cluster')
  dbscan_run2_results.gpkg (cluster column: 'cluster', noise = -1)
  hdbscan_results.gpkg     (cluster column: 'cluster', noise = -1)

Output per method:
  <method>_zones.gpkg      — one point per zone (centroid + W_c)
  <method>_zones.csv       — tabular summary
============================================================
"""

import matplotlib
matplotlib.use("Agg")

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ── Configuration ─────────────────────────────────────────
BASE   = r"C:\Users\atefe\OneDrive\Desktop\Beuth\Masterarbeit\cluster_analysis"
OUTDIR = os.path.join(BASE, "attraction_results")
os.makedirs(OUTDIR, exist_ok=True)

METHODS = [
    {
        "name":   "kmeans",
        "gpkg":   os.path.join(BASE, "kmeans",               "kmeans_results.gpkg"),
        "label":  "K-Means  (k=13)",
    },
    {
        "name":   "dbscan",
        "gpkg":   os.path.join(BASE, "dbscan",               "dbscan_run2_results.gpkg"),
        "label":  "DBSCAN   (eps=515m, MinPts=5)",
    },
    {
        "name":   "hdbscan",
        "gpkg":   os.path.join(BASE, "hdbscan5",             "hdbscan_results.gpkg"),
        "label":  "HDBSCAN  (mpts=mclSize=50, EOM)",
    },
]

# ── Helper: aggregate one method ──────────────────────────
def aggregate_method(cfg):
    name  = cfg["name"]
    label = cfg["label"]
    gpkg  = cfg["gpkg"]

    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")

    # Load
    gdf = gpd.read_file(gpkg)
    crs = gdf.crs
    print(f"  Features loaded : {len(gdf)}")
    print(f"  CRS             : {crs}")

    # Check attraction_weight exists
    if "attraction_weight" not in gdf.columns:
        print("  ERROR: 'attraction_weight' column not found!")
        print(f"  Available columns: {list(gdf.columns)}")
        return None

    # Separate noise from clusters
    noise_mask    = gdf["cluster"] == -1
    gdf_clustered = gdf[~noise_mask].copy()
    n_noise       = noise_mask.sum()
    n_clustered   = len(gdf_clustered)
    n_clusters    = gdf_clustered["cluster"].nunique()

    print(f"  Clusters        : {n_clusters}")
    print(f"  Clustered POIs  : {n_clustered}")
    print(f"  Noise (excluded): {n_noise}")

    # W_c = sum(w_i for i in c)  — core formula
    zone_stats = (
        gdf_clustered
        .groupby("cluster")
        .agg(
            n_poi          = ("attraction_weight", "count"),
            W_c            = ("attraction_weight", "sum"),
            W_c_mean       = ("attraction_weight", "mean"),
            centroid_x     = ("geometry", lambda g: g.x.mean()),
            centroid_y     = ("geometry", lambda g: g.y.mean()),
        )
        .reset_index()
    )
    zone_stats["W_c_share_pct"] = (
        zone_stats["W_c"] / zone_stats["W_c"].sum() * 100
    ).round(2)

    return zone_stats, crs, n_noise, n_clustered


def save_and_print(zone_stats, crs, n_noise, n_clustered, cfg):
    name  = cfg["name"]
    label = cfg["label"]

    # ── Print thesis table ────────────────────────────────
    print(f"\n  Zone attraction weights  (W_c = sum of w_i):")
    print(f"  {'Zone':>5}  {'n_POI':>6}  {'W_c':>12}  {'Share(%)':>9}")
    print("  " + "-"*38)
    for _, row in zone_stats.iterrows():
        print(f"  {int(row['cluster']):>5}  {int(row['n_poi']):>6}  "
              f"{row['W_c']:>12.1f}  {row['W_c_share_pct']:>8.2f}%")
    print("  " + "-"*38)
    print(f"  {'TOTAL':>5}  {int(zone_stats['n_poi'].sum()):>6}  "
          f"{zone_stats['W_c'].sum():>12.1f}  {'100.00%':>9}")
    print(f"\n  Noise POIs excluded: {n_noise}  "
          f"(attraction weight omitted: "
          f"{cfg.get('noise_weight', 'see gpkg')})")

    # ── Save CSV ──────────────────────────────────────────
    csv_path = os.path.join(OUTDIR, f"{name}_zones.csv")
    zone_stats.to_csv(csv_path, index=False)
    print(f"\n  CSV saved : {csv_path}")

    # ── Save GeoPackage (zone centroids) ──────────────────
    from shapely.geometry import Point
    zone_stats["geometry"] = zone_stats.apply(
        lambda r: Point(r["centroid_x"], r["centroid_y"]), axis=1
    )
    gdf_zones = gpd.GeoDataFrame(zone_stats, crs=crs)
    gpkg_path = os.path.join(OUTDIR, f"{name}_zones.gpkg")
    gdf_zones.to_file(gpkg_path, driver="GPKG")
    print(f"  GPKG saved: {gpkg_path}")

    return zone_stats


# ── Bar chart: W_c distribution per method ────────────────
def plot_attraction(zone_stats, cfg, ax):
    name  = cfg["name"]
    label = cfg["label"]

    ax.bar(zone_stats["cluster"].astype(str),
           zone_stats["W_c"],
           color="#1a3a5c", edgecolor="white", linewidth=0.5)
    ax.set_title(label, fontsize=9, fontfamily="serif")
    ax.set_xlabel("Cluster", fontsize=8, fontfamily="serif")
    ax.set_ylabel("$W_c$ (attraction weight)", fontsize=8, fontfamily="serif")
    ax.tick_params(labelsize=7, axis="x", rotation=90)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis="y", color="#eeeeee", linewidth=0.5)


# ── MAIN ──────────────────────────────────────────────────
all_stats = {}

for cfg in METHODS:
    result = aggregate_method(cfg)
    if result is None:
        continue
    zone_stats, crs, n_noise, n_clustered = result

    # compute noise attraction weight separately for info
    gdf_full = gpd.read_file(cfg["gpkg"])
    noise_w  = gdf_full[gdf_full["cluster"] == -1]["attraction_weight"].sum() \
               if "attraction_weight" in gdf_full.columns else 0
    cfg["noise_weight"] = f"{noise_w:.1f}"

    zone_stats = save_and_print(zone_stats, crs, n_noise, n_clustered, cfg)
    all_stats[cfg["name"]] = zone_stats


# ── Combined bar chart ────────────────────────────────────
n_methods = len(all_stats)
if n_methods > 0:
    fig, axes = plt.subplots(1, n_methods,
                             figsize=(5 * n_methods, 5))
    if n_methods == 1:
        axes = [axes]

    for ax, (name, stats) in zip(axes, all_stats.items()):
        cfg_match = next(c for c in METHODS if c["name"] == name)
        plot_attraction(stats, cfg_match, ax)

    fig.suptitle(
        "Attraction Weight Distribution per Zone — $W_c = \\sum_{i \\in c} w_i$",
        fontsize=11, fontfamily="serif", y=1.02
    )
    plt.tight_layout()
    chart_path = os.path.join(OUTDIR, "attraction_weights_comparison.png")
    plt.savefig(chart_path, dpi=300, bbox_inches="tight", facecolor="white")
    print(f"\nComparison chart saved: {chart_path}")

print("\n✓ Attraction aggregation complete.")
print(f"  All outputs in: {OUTDIR}")
