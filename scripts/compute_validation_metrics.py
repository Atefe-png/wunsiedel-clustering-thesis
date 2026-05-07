"""
============================================================
Validation Metrics -- Silhouette & Davies-Bouldin Index
------------------------------------------------------------
Thesis: Zaeemi (2026), Section 5.3
Author: Atefeh Zaeemi, BHT Berlin, in cooperation with atSTAKE

Reads clustering results from outputs/ and computes:
  - Silhouette Coefficient (higher = better, range -1 to 1)
  - Davies-Bouldin Index   (lower = better, min 0)

Expected results (verified from thesis CSV):
  K-Means : Silhouette=0.573, DB=0.624
  DBSCAN  : Silhouette=0.577, DB=0.375
  HDBSCAN : Silhouette=0.756, DB=0.324

Run AFTER all three clustering scripts have been executed.
Output: outputs/validation_metrics.csv
============================================================
"""

import os
import csv
import warnings
import geopandas as gpd
import numpy as np
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data", "processed")
OUT_DIR  = os.path.join(ROOT, "outputs")

FILES = {
    "K-Means": os.path.join(OUT_DIR, "kmeans_results.gpkg"),
    "DBSCAN":  os.path.join(OUT_DIR, "dbscan_run2_results.gpkg"),
    "HDBSCAN": os.path.join(OUT_DIR, "hdbscan_results.gpkg"),
}

# ── Load base POI dataset ─────────────────────────────────────
print("Loading POI dataset ...")
poi = gpd.read_file(os.path.join(DATA_DIR, "wue_poi_clean.gpkg"))
coords_raw = np.column_stack([poi.geometry.x, poi.geometry.y])
scaler     = StandardScaler()
coords_std = scaler.fit_transform(coords_raw)

# ── Compute metrics ───────────────────────────────────────────
results = []
for method, fpath in FILES.items():
    if not os.path.exists(fpath):
        print(f"MISSING: {fpath} -- run the clustering script first.")
        continue
    print(f"\n{method} ...")
    gdf    = gpd.read_file(fpath)
    labels = gdf["cluster"].values

    n_noise    = int(np.sum(labels == -1))
    noise_pct  = round(100 * n_noise / len(labels), 1)
    mask       = labels != -1
    labels_cl  = labels[mask]
    n_zones    = len(np.unique(labels_cl))

    # DBSCAN uses raw metres; others use standardised coords
    coords = coords_raw if method == "DBSCAN" else coords_std
    coords_cl = coords[mask]

    sil = silhouette_score(coords_cl, labels_cl)
    db  = davies_bouldin_score(coords_cl, labels_cl)

    print(f"  Zones={n_zones}, Noise={n_noise} ({noise_pct}%)")
    print(f"  Silhouette={sil:.4f}, Davies-Bouldin={db:.4f}")

    results.append({
        "Method": method, "Zones": n_zones,
        "Noise_n": n_noise, "Noise_pct": noise_pct,
        "Silhouette": round(sil, 4),
        "DaviesBouldin": round(db, 4),
    })

# ── Save CSV ──────────────────────────────────────────────────
out_csv = os.path.join(OUT_DIR, "validation_metrics.csv")
if results:
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved: {out_csv}")

# ── Print summary ─────────────────────────────────────────────
print("\n" + "="*62)
print(f"{'Method':<10} {'Zones':>5} {'Noise%':>7} "
      f"{'Silhouette':>11} {'DB-Index':>9}")
print("-"*62)
for r in results:
    print(f"{r['Method']:<10} {r['Zones']:>5} {r['Noise_pct']:>6.1f}% "
          f"{r['Silhouette']:>11.4f} {r['DaviesBouldin']:>9.4f}")
print("="*62)
