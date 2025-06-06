# Predicting-datasets-for-OpenStreetMaps-Thesis-2025

This project evaluates hierarchical vs. flat tag–recommendation models for
OpenStreetMap (OSM).  


This repository contains all code needed to reproduce the experiments that compare a hierarchical Louvain-based tag recommender with a traditional flat model for OpenStreetMap (OSM).  
Large data artefacts (OSM extracts, compiled protobuf schemata, etc.) are not stored in Git; `make` targets download or rebuild them automatically.


Prerequisites:
1. Git ≥ 2.30
2. Conda / Mamba (or any Python 3.10+ environment)
3. GNU Make (comes with every Linux / macOS, on Windows use WSL or make from MSYS2)
4. Go >=1.21 -> automatically installed with "make env"

HOW TO START:
# 1. clone the repo
git clone https://github.com/DenisAkmaikin/Predicting-datasets-for-OpenStreetMaps-Thesis-2025.git
cd Predicting-datasets-for-OpenStreetMaps-Thesis-2025

# 2. create & activate the Conda environment 
make env
conda activate osm-tags          # or "mamba activate osm-tags"

# 3. download sample data, build the recommender, run evaluation (~6 GB disk)
make all                         # = download-osm  +  build-graph + build-schema + evaluate

# metrics written to:  output/metrics_*.csv

! Common "make" targets:
env	-> create Conda env and install Go + Python deps
download-osm ->	fetches the Amsterdam .osm.pbf extract (≈ 170 MB)
build-graph	-> builds tag co-occurrence graph JSON from the extract
build-schema ->	runs Louvain, compiles hierarchical schema (*.pb)
evaluate-flat ->	evaluates flat model – writes metrics_flat.csv
evaluate-tree	-> evaluates hierarchical model – writes metrics_tree*.csv
evaluate	-> runs both evaluations at the default K settings
clean	-> removes all build artefacts (keeps downloaded data)

LARGE FILES:

Amsterdam OSM extract (`amsterdam.osm.pbf`) -> 170 MB  -> `make download-osm`                              
Full tag TSV / JSONL  ->  500 MB – 2 GB -> produced by `build-graph`
Pre-trained schema (`tags.tsv.schemaTree.typed.pb`) ->  105 MB   -> produced by `build-schema`                       







