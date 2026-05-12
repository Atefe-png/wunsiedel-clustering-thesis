<<<<<<< HEAD
# OSM-Based POI Clustering for Rural Travel Demand Modelling
### Case Study: Landkreis Wunsiedel im Fichtelgebirge, Bavaria

**Master's thesis** — Atefeh Zaeemi  
Berliner Hochschule für Technik (BHT), Fachbereich III, 2026  
Supervised by Prof. Dr. Florian Hruby  
Developed in cooperation with **atSTAKE**
=======
# Spatial Clustering for Rural Travel Demand Modelling
### A Case Study: Landkreis Wunsiedel im Fichtelgebirge

This repository accompanies my master's thesis submitted at the 
Berliner Hochschule für Technik (BHT Berlin) in the Master's 
programme Geoinformation (2025).

The thesis investigates whether OpenStreetMap data alone can serve 
as a basis for generating attraction weight zones in simplified 
travel demand models — a question that matters particularly in 
rural districts where official data sources are often inaccessible 
or incomplete.
>>>>>>> 7d4c71427e5c7f364f6810a26bed549339d848db

---

## What this project does

<<<<<<< HEAD
This repository contains all Python scripts and the interactive dashboard
for comparing three spatial clustering methods applied to OpenStreetMap (OSM)
Point of Interest (POI) data in a rural German district.

**Research question:** Which clustering method best derives meaningful
destination zones and attraction weights for simplified travel demand models
in rural areas — where data is sparse and settlement patterns are irregular?

**Three methods are compared:**
- K-Means (k=13)
- DBSCAN (ε=515 m, MinPts=5)
- HDBSCAN (mpts=50, mclSize=50)

The resulting zones are used to estimate *attraction weights* (Wc) —
a key input to the four-step Ver_Bau / Bosserhoff travel demand framework.

---

## How the parameters were determined

### K-Means — k=13

The number of clusters was not chosen arbitrarily. Two methods were applied:

1. **Elbow Method (WCSS):** The within-cluster sum of squares was computed
   for k = 2 to 25. The "elbow" — where adding more clusters gives little
   improvement — was identified at **k=13** using the Kneedle algorithm
   (Satopaa et al. 2011). WCSS at k=13: 3,320,218.

2. **Silhouette Analysis:** The silhouette coefficient was computed for
   k = 2 to 25 to cross-validate the elbow result. k=13 returned a
   Silhouette score of 0.573 and Davies-Bouldin index of 0.624, confirming
   a stable, meaningful partition.

Other parameters:
- `init='k-means++'` — smart seeding to avoid poor local minima
  (Arthur & Vassilvitskii 2007)
- `n_init=20` — 20 independent runs; best result is kept
- `random_state=42` — fixed seed for full reproducibility

### DBSCAN — ε=515 m, MinPts=5

DBSCAN groups points that lie within ε metres of at least MinPts neighbours.

**MinPts=5** is the canonical recommendation for 2D spatial data
(Ester et al. 1996) and was kept fixed across all runs.

**ε=515 m** was determined from the **k-distance graph**:
- For each of the 2,673 POIs, the distance to its 5th nearest neighbour
  (k=MinPts) was computed
- These distances were sorted in ascending order and plotted
- The "elbow" in this curve marks the density threshold: points to the
  left are in dense regions (clusters), points to the right are isolated
  (noise). The elbow was visually identified at **515 metres**.

A **sensitivity analysis** with three runs confirmed the choice:

| Run | ε (m) | Clusters | Noise | Selected |
|-----|-------|----------|-------|----------|
| 1   | 412   | varies   | high  |          |
| 2   | 515   | 64       | 13.0% | ✓ primary |
| 3   | 618   | fewer    | low   |          |

Run 2 (ε=515 m) was selected because it produced the best spatial
coherence and the most interpretable zone structure for this rural area.

Note: DBSCAN was applied in **raw EPSG:25832 coordinates (metres)**, so ε
is directly meaningful as a real-world distance — no standardisation needed.

### HDBSCAN — mpts=50, mclSize=50

HDBSCAN (Campello et al. 2013) extends DBSCAN by building a full
density hierarchy and extracting only the most stable clusters.

**min_cluster_size (mclSize):** Controls the smallest allowable cluster.
Four values were tested: 6, 8, 50, 100. Small values (6, 8) produced
many micro-clusters reflecting local noise. Large values (100) were too
coarse for the settlement structure of Wunsiedel. **mclSize=50** best
captured functional destination zones at the rural district scale.

**min_samples (mpts):** Controls how conservative the noise labelling is.
Following Campello et al. (2013), **mpts was set equal to mclSize (=50)**,
meaning both parameters were always varied jointly, not independently.

Result: 11 clusters, 33.8% noise — the high noise share is a valid
scientific finding, not a calibration failure. It reflects genuine spatial
discontinuity in rural POI distributions.

---

## Key results

| Method  | Zones | Noise | Silhouette ↑ | Davies-Bouldin ↓ | ΣWc |
|---------|-------|-------|-------------|-----------------|-----|
| K-Means | 13    | 0%    | 0.573       | 0.624           | 3,320,218 |
| DBSCAN  | 64    | 13.0% | 0.577       | 0.375           | 2,712,091 |
| HDBSCAN | 11    | 33.8% | **0.756**   | **0.324**       | 2,300,151 |

HDBSCAN achieved the best internal validation scores. DBSCAN's 64 zones
reflect its structural sensitivity to spatial heterogeneity in rural areas.
K-Means provides the most operationally compact result (13 zones, no noise).
=======
Three spatial clustering algorithms — K-Means, DBSCAN, and HDBSCAN 
— are applied to a cleaned dataset of 2,673 OSM-derived points of 
interest (POIs) covering Landkreis Wunsiedel im Fichtelgebirge in 
northeastern Bavaria. The resulting cluster zones are used to 
compute attraction weights following the Ver_Bau/Bosserhoff 
framework, and the three methods are systematically compared in 
terms of spatial coherence, parameter sensitivity, and practical 
suitability for transport planning applications.

---

## Study area

Landkreis Wunsiedel im Fichtelgebirge is a rural district in 
northeastern Bavaria with a polycentric settlement structure, 
low population density, and limited public transport coverage. 
Its spatial heterogeneity — a dense commercial corridor along 
the Marktredwitz–Selb axis surrounded by forested, sparsely 
settled terrain — makes it a demanding test case for clustering 
methods that were largely developed and evaluated in urban contexts.

---

## Methods and results

| Method  | Parameters           | Clusters | Noise  |
|---------|----------------------|----------|--------|
| K-Means | k = 13               | 13       | 0%     |
| DBSCAN  | ε = 515 m, MinPts = 5| 64       | 13.0%  |
| HDBSCAN | mpts = mclSize = 50  | 11       | 33.8%  |

All three methods consistently identify the Marktredwitz–Selb 
corridor as the dominant destination zone, capturing between 
33.7% and 39.5% of total modelled attraction weight.
>>>>>>> 7d4c71427e5c7f364f6810a26bed549339d848db

---

## Repository structure
<<<<<<< HEAD

```
wunsiedel-atStake/
│
├── scripts/
│   ├── 01_data_cleaning.py           ← Deduplication → wue_poi_clean.gpkg
│   ├── 02_determine_k_kmeans.py      ← How k=13 was found (Elbow + Silhouette + DB)
│   ├── 03_determine_eps_dbscan.py    ← How ε=515m was found (k-dist graph)
│   ├── kmeans_clustering.py          ← K-Means clustering (k=13)
│   ├── dbscan_clustering.py          ← DBSCAN (3 sensitivity runs)
│   ├── hdbscan_clustering.py         ← HDBSCAN (mpts=mclSize=50)
│   ├── compute_validation_metrics.py ← Silhouette + DB Index
│   └── attraction_aggregation.py     ← W_c = sum(w_i) per zone
│
├── data/
│   └── processed/
│       └── wue_poi_clean.gpkg        ← place file here (see below)
│
├── outputs/                          ← generated automatically by scripts
│   ├── kmeans_results.gpkg
│   ├── dbscan_run2_results.gpkg
│   ├── hdbscan_results.gpkg
│   ├── validation_metrics.csv
│   └── *.png / *.pdf
│
├── dashboard/
│   ├── index.html                    ← open in browser
│   ├── app.js
│   ├── style.css
│   └── data.js
│
├── requirements.txt
└── README.md
```

---

## Setup and usage

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add the POI data file

Place `wue_poi_clean.gpkg` into `data/processed/`.  
This file contains 2,673 deduplicated POI features in EPSG:25832 (UTM Zone 32N),
derived from the OSM Geofabrik Bayern extract (November 2025) and processed
using the OSM extraction pipeline (see thesis Section 4).

### 3. Run the scripts in order

```bash
# Step 1 — Data cleaning (run once to generate wue_poi_clean.gpkg)
python scripts/01_data_cleaning.py

# Step 2 — Parameter selection: how k=13 was determined
python scripts/02_determine_k_kmeans.py

# Step 3 — Parameter selection: how ε=515m was determined
python scripts/03_determine_eps_dbscan.py

# Step 4 — Run the three clustering methods
python scripts/kmeans_clustering.py
python scripts/dbscan_clustering.py
python scripts/hdbscan_clustering.py

# Step 5 — Compute validation metrics
python scripts/compute_validation_metrics.py

# Step 6 — Compute attraction weights per zone
python scripts/attraction_aggregation.py
```

All outputs are saved automatically to `outputs/`.

### 4. Open the dashboard

Open `dashboard/index.html` in any browser (double-click).  
The map shows all 2,673 POIs with all three clustering results
and attraction weights as an interactive Leaflet.js visualisation.

**Note:** Uses CartoDB Positron basemap tiles (not OSM tiles, which
block local file access).
=======
wunsiedel-clustering-thesis/
├── scripts/            Python scripts for extraction,
│                       cleaning, and clustering
├── data/
│   └── processed/      Cleaned POI dataset and
│                       clustering outputs (CSV, GeoPackage)
├── dashboard/          Interactive Leaflet.js web map
└── requirements.txt    Python dependencies
---

## Interactive map

The clustering results can be explored interactively at:  
 https://atefe-png.github.io/wunsiedel-dashboard/
>>>>>>> 7d4c71427e5c7f364f6810a26bed549339d848db

---

## Data sources

<<<<<<< HEAD
- **OSM data:** © OpenStreetMap contributors, ODbL licence.
  Downloaded via Geofabrik (geofabrik.de), Bayern, November 2025.
- **Administrative boundary:** Landkreis Wunsiedel im Fichtelgebirge,
  Bayern, Germany.
- **POI categories:** Retail, health, education, offices, leisure,
  industrial/commercial sites — selected per Ver_Bau / Bosserhoff (2023)
  attraction weight framework.

---

## References

- Campello, R.J.G.B., Moulavi, D., Sander, J. (2013). Density-Based
  Clustering Based on Hierarchical Density Estimates. PAKDD 2013.
- Ester, M., Kriegel, H.-P., Sander, J., Xu, X. (1996). A density-based
  algorithm for discovering clusters in large spatial databases with noise.
  KDD-96.
- Klinkhardt, C. et al. (2021). Using OpenStreetMap as a data source for
  attractiveness in travel demand models. ISPRS IJGI 10(8).
- MacQueen, J. (1967). Some methods for classification and analysis of
  multivariate observations. Proc. 5th Berkeley Symposium.
- Satopaa, V. et al. (2011). Finding a "kneedle" in a haystack.
  ICDCS Workshops.
- Zaeemi, A. (2026). Suitability of OpenStreetMap Data for Deriving
  Traffic Attraction Potentials in Rural Areas. Master's thesis, BHT Berlin.
=======
- POI data: OpenStreetMap via Geofabrik Bayern extract (November 2025)
- District boundary: Official administrative boundaries, EPSG:25832
- Satellite imagery (validation only): Google Maps

---

*Atefeh Zaeemi — BHT Berlin, Fachbereich III*
>>>>>>> 7d4c71427e5c7f364f6810a26bed549339d848db
