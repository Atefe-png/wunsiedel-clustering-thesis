# Scripts

Python scripts for POI extraction, cleaning, and clustering.

## Order of execution
1. `01_poi_extraction.py` — Extract POIs from OSM Geofabrik data
2. `02_poi_cleaning.py` — Clean and filter POI dataset
3. `03_kmeans_clustering.py` — K-Means clustering (k=13)
4. `04_dbscan_clustering.py` — DBSCAN clustering (ε=515m)
5. `05_hdbscan_clustering.py` — HDBSCAN clustering (mpts=50)
6. `06_attraction_weights.py` — Compute attraction weights
