"""
============================================================
Attraction Weight Aggregation — W_c = sum(w_i for i in c)
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 4.5
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

Based on: Bosserhoff (2023), Klinkhardt et al. (2021)

WHAT THIS SCRIPT DOES
----------------------
For each clustering method (K-Means, DBSCAN, HDBSCAN):
  1. Loads the GeoPackage with cluster labels
  2. Computes W_c = sum of attraction_weight per cluster
  3. Computes cluster centroid (geometric mean of members)
  4. Saves results as CSV and GeoPackage (zone centroids)
  5. Prints thesis-ready summary table

KEY RESULTS (verified from thesis):
  K-Means : ΣWc = 3,320,218  (13 zones, 0 noise)
  DBSCAN  : ΣWc = 2,712,091  (64 zones, 13.0% noise)
  HDBSCAN : ΣWc = 2,300,151  (11 zones, 33.8% noise)

Run AFTER all three clustering scripts have been executed.

Input:  outputs/kmeans_results.gpkg
        outputs/dbscan_run2_results.gpkg
        outputs/hdbscan_results.gpkg
Output: outputs/attraction_results/<method>_zones.gpkg
        outputs/attraction_results/<method>_zones.csv
        outputs/attraction_results/attraction_weights_comparison.png
============================================================
"""

import matplotlib
matplotlib.use("Agg")
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from shapely.geometry import Point

# ── Paths (relative to this script) ─────────────────────────
ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "outputs", "attraction_results")
os.makedirs(OUTDIR, exist_ok=True)

METHODS = [
    {
        "name":  "kmeans",
        "gpkg":  os.path.join(ROOT, "outputs", "kmeans_results.gpkg"),
        "label": "K-Means (k=13)",
    },
    {
        "name":  "dbscan",
        "gpkg":  os.path.join(ROOT, "outputs", "dbscan_run2_results.gpkg"),
        "label": "DBSCAN (eps=515m, MinPts=5)",
    },
    {
        "name":  "hdbscan",
        "gpkg":  os.path.join(ROOT, "outputs", "hdbscan_results.gpkg"),
        "label": "HDBSCAN (mpts=mclSize=50)",
    },
]

# ── Helper: aggregate one method ─────────────────────────────
def aggregate_method(cfg):
    name, label, gpkg = cfg["name"], cfg["label"], cfg["gpkg"]

    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")

    if not os.path.exists(gpkg):
        print(f"  MISSING: {gpkg}")
        print(f"  → Run the clustering script first.")
        return None

    gdf = gpd.read_file(gpkg)
    print(f"  Features : {len(gdf)} | CRS: {gdf.crs}")

    if "attraction_weight" not in gdf.columns:
        print(f"  ERROR: 'attraction_weight' column not found!")
        print(f"  Available columns: {list(gdf.columns)}")
        return None

    noise_mask    = gdf["cluster"] == -1
    gdf_clustered = gdf[~noise_mask].copy()
    n_noise       = int(noise_mask.sum())
    n_clusters    = gdf_clustered["cluster"].nunique()

    print(f"  Clusters : {n_clusters} | Noise excluded: {n_noise}")

    # W_c = sum(w_i for i in c)
    zone_stats = (
        gdf_clustered
        .groupby("cluster")
        .agg(
            n_poi      = ("attraction_weight", "count"),
            W_c        = ("attraction_weight", "sum"),
            centroid_x = ("geometry", lambda g: g.x.mean()),
            centroid_y = ("geometry", lambda g: g.y.mean()),
        )
        .reset_index()
    )
    zone_stats["W_c_share_pct"] = (
        zone_stats["W_c"] / zone_stats["W_c"].sum() * 100
    ).round(2)

    return zone_stats, gdf.crs, n_noise

# ── Save + print ──────────────────────────────────────────────
def save_and_print(zone_stats, crs, n_noise, cfg):
    name, label = cfg["name"], cfg["label"]

    print(f"\n  {'Zone':>5}  {'n_POI':>6}  {'W_c':>12}  {'Share':>8}")
    print("  " + "-"*38)
    for _, row in zone_stats.iterrows():
        print(f"  {int(row['cluster']):>5}  {int(row['n_poi']):>6}  "
              f"{row['W_c']:>12.1f}  {row['W_c_share_pct']:>7.2f}%")
    print("  " + "-"*38)
    print(f"  {'TOTAL':>5}  {int(zone_stats['n_poi'].sum()):>6}  "
          f"{zone_stats['W_c'].sum():>12.1f}  {'100.00%':>8}")

    # CSV
    csv_path = os.path.join(OUTDIR, f"{name}_zones.csv")
    zone_stats.to_csv(csv_path, index=False)
    print(f"\n  CSV  saved: {csv_path}")

    # GeoPackage
    zone_stats["geometry"] = zone_stats.apply(
        lambda r: Point(r["centroid_x"], r["centroid_y"]), axis=1)
    gdf_zones = gpd.GeoDataFrame(zone_stats, crs=crs)
    gpkg_path = os.path.join(OUTDIR, f"{name}_zones.gpkg")
    gdf_zones.to_file(gpkg_path, driver="GPKG")
    print(f"  GPKG saved: {gpkg_path}")

    return zone_stats

# ── MAIN ─────────────────────────────────────────────────────
all_stats = {}

for cfg in METHODS:
    result = aggregate_method(cfg)
    if result is None:
        continue
    zone_stats, crs, n_noise = result
    zone_stats = save_and_print(zone_stats, crs, n_noise, cfg)
    all_stats[cfg["name"]] = zone_stats

# ── Combined bar chart ────────────────────────────────────────
if all_stats:
    n = len(all_stats)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]
    for ax, (name, stats) in zip(axes, all_stats.items()):
        cfg_m = next(c for c in METHODS if c["name"] == name)
        ax.bar(stats["cluster"].astype(str), stats["W_c"],
               color="#1a3a5c", edgecolor="white", linewidth=0.5)
        ax.set_title(cfg_m["label"], fontsize=9, fontfamily="serif")
        ax.set_xlabel("Cluster", fontsize=8)
        ax.set_ylabel("$W_c$", fontsize=8)
        ax.tick_params(labelsize=7, axis="x", rotation=90)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, axis="y", color="#eeeeee", linewidth=0.5)
    fig.suptitle(
        "Attraction Weight per Zone — $W_c = \\sum_{i \\in c} w_i$",
        fontsize=11, fontfamily="serif")
    plt.tight_layout()
    chart = os.path.join(OUTDIR, "attraction_weights_comparison.png")
    plt.savefig(chart, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(chart.replace(".png", ".pdf"), bbox_inches="tight")
    print(f"\nChart saved: {chart}")

print("\nDone. All outputs in: outputs/attraction_results/")
