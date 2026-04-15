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

---

## What this project does

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

---

## Repository structure
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
🗺️ https://atefe-png.github.io/wunsiedel-dashboard/

---

## Data sources

- POI data: OpenStreetMap via Geofabrik Bayern extract (November 2025)
- District boundary: Official administrative boundaries, EPSG:25832
- Satellite imagery (validation only): Google Maps

---

*Atefeh Zaeemi — BHT Berlin, Fachbereich III*
