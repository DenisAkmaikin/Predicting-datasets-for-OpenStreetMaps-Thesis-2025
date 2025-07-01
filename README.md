# Predicting OSM Tags with the Louvain Method
_Bachelor thesis - Vrije Universiteit Amsterdam (2025)_ by Denis Akmaikin(denis.akmaikin@gmail.com)

This repo reproduces **“Building a Hierarchial Recommender for OpenStreetMap Tags with the Louvain Method”**.  
It builds a tag co-occurrence graph for the Netherlands, derives a Louvain/Leiden
hierarchy, and benchmarks it against a flat-frequency baseline.

#Run the commands in the terminal (I used vscode)


Requierments:

| Resource | Requirement                                          |
| -------- | ---------------------------------------------------- |
| RAM      | 8 GB minimum, 16 GB recommended                      |
| Disk     | 10+ GB free (especially for .pbf files + graphs)     |
| CPU      | 4+ cores recommended (for server + evaluation speed) |

(This thesis has been tested on Ubuntu 20.04.1)
## 1. Quick start (Linux / macOS)

```bash
git clone https://github.com/DenisAkmaikin/Predicting-datasets-for-OpenStreetMaps-Thesis-2025.git
cd RecommenderServer-main  #(go to the root of the repository)


#first make a conda enviornment

```bash

conda env create -f environment.yml --name reco-thesis
conda activate reco-thesis

         

#DATA

# Download NL extract (~1.3 GB)
wget https://download.geofabrik.de/europe/north-holland-latest.osm.pbf

#Paste this into the terminal
cat <<EOF > osmium_config.json
{
  "output": {
    "omitmetadata": true,
    "geometry": false,
    "format": "jsonseq"
  }
}
EOF


# Extract tags only 
osmium export pipeline/data/north-holland-latest.osm.pbf \
  -f jsonseq -c osmium_config.json \
  | gzip > assets/osm_tags.json.gz

#Building Graph and Hierarchy

# Count co-occurrences – creates assets/graphs/osm_edges.json
python pipeline/build_graph_sqlite.py \
  --tags assets/osm_tags.json.gz \
  --edges assets/graphs/osm_edges.json \
  --min_count 5

#gamma sweep
for G in 0.5 1.0 1.4 2.0; do
  echo " -> Building γ=$G"
  python pipeline/build_hierarchy.py \
    --edges assets/graphs/osm_edges.json \
    --tree  assets/hierarchies/osm_louvain_gamma${G}.json \
    --gamma ${G}
done

# Use gamma = 1.0 by default or can just change the 1.0
ln -sf assets/hierarchies/osm_louvain_gamma1.0.json assets/hierarchies/osm_louvain.json

#(Forest-fire below)

#RUn servers

go build -o RecoSrv main.go   # To compile the server

pkill -f "./RecoSrv serve" || true   #kill old servers (optional)


# Start hierarchy server (port 8080)
./RecoSrv serve pipeline/data/tags.tsv.schemaTree.typed.pb \
  --mode hierarchy -p 8080 > /tmp/reco_hier.log 2>&1 &

# Start flat server (port 8081)
./RecoSrv serve pipeline/data/tags.tsv.schemaTree.typed.pb \
  --mode flat -p 8081 > /tmp/reco_flat.log 2>&1 &

#generate eval sets
python scripts/make_eval_balanced.py        
python scripts/make_eval_complex.py   

#Evaluation helper function, paste it once in the terminal:

run_eval () {
  local TSV=$1
  local SUITE=$2
  local PORT=$3
  local MODE=$4
  local K=$5
  local METRIC=$6
  local OUT=results/${MODE}_${SUITE}_${METRIC}${K}.csv
  python evaluate.py \
    --evalfile "${TSV}" \
    --outfile  "${OUT}" \
    --topk ${K} --metric ${METRIC} \
    --server http://localhost:${PORT}/recommender
  echo " -> ${OUT}"
}

#Run full evaluation:

for SUITE in balanced complex; do
  TSV=pipeline/data/eval_${SUITE}.tsv
  run_eval $TSV $SUITE 8080 hier 3  prec
  run_eval $TSV $SUITE 8080 hier 10 map
  run_eval $TSV $SUITE 8080 hier 10 ndcg
  run_eval $TSV $SUITE 8081 flat 3  prec
  run_eval $TSV $SUITE 8081 flat 10 map
  run_eval $TSV $SUITE 8081 flat 10 ndcg
done


#Run this to get the evaluation summary:

echo -e "\n Evaluation Summary:\n"

for MODE in flat hier; do
  for SUITE in balanced complex; do
    for METRIC in prec map ndcg; do
      for K in 3 10; do
        FILE="results/${MODE}_${SUITE}_${METRIC}${K}.csv"
        if [ -f "$FILE" ]; then
          SCORE=$(tail -n +2 "$FILE" | cut -d',' -f2 | awk '{s+=$1} END {printf "%.4f", s/NR}')
          echo "${MODE^^} | ${SUITE^^} | ${METRIC^^}@${K} -> $SCORE"
        fi
      done
    done
  done
done



#results are saved here -> results/{mode}_{suite}_{metric}{k}.csv



#Other test commands


#generates a wordcloud from a cluster
python scripts/cluster_wordcloud.py


# to get a comparison of top 10 suggestions of a random tag
python compare_suggestions.py \
  --sample pipeline/data/eval_complex.tsv \
  --top 10



#Forest-Fire run
# Forest-fire 6% sample  #Warning this will take a very long time
python scripts/sample_forest_fire_fast.py \
       --src assets/graphs/osm_edges.json \
       --dest assets/graphs/osm_edges_ff.json \
       --p 0.45 --target 0.06 #this is the % of graph kept

#If you do the forest-fire, after it samples the graph build it like this
python pipeline/build_hierarchy.py \
  --edges assets/graphs/osm_edges_ff.json \
  --tree  assets/hierarchies/osm_louvain_ff.json \
  --gamma 1.0 #(or choose another gamma value)

#optionally can symlink it
ln -sf assets/hierarchies/osm_louvain_ff.json assets/hierarchies/osm_louvain.json

#Restart the server
pkill -f "./RecoSrv serve" || true

./RecoSrv serve pipeline/data/tags.tsv.schemaTree.typed.pb \
  --mode hierarchy -p 8080 > /tmp/reco_hier_ff.log 2>&1 &

sleep 6

#Paste the helper function from above ---> run_eval()

#THen run 
for SUITE in balanced complex; do
  TSV=pipeline/data/eval_${SUITE}.tsv
  run_eval $TSV $SUITE 8080 hier 3  prec
  run_eval $TSV $SUITE 8080 hier 10 map
  run_eval $TSV $SUITE 8080 hier 10 ndcg
done

#THen check results.

echo -e "\n Forest Fire Summary:\n"

for SUITE in balanced complex; do
  for METRIC in prec map ndcg; do
    for K in 3 10; do
      FILE="results/hier_${SUITE}_${METRIC}${K}_ff.csv"
      if [ -f "$FILE" ]; then
        SCORE=$(tail -n +2 "$FILE" | cut -d',' -f2 | awk '{s+=$1} END {printf "%.4f", s/NR}')
        echo "HIER_FF | ${SUITE^^} | ${METRIC^^}@${K} -> $SCORE"
      fi
    done
  done
done

#This concludes the experiments, and pipeline recreation.