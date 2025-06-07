# -------------------- project-wide Makefile --------------------
.PHONY: env install serve-hier eval-hier figures clean \
        build-graph build-hierarchy evaluate-small

# ── 1 Environment ─────────────────────────────────────────────────────
env: install
install:
	conda env create -f environment.yml --name reco-thesis || true

# ── 2 Run server + evaluation ────────────────────────────────────────
serve-hier:
	./RecoSrv serve pipeline/data/tags.tsv.schemaTree.typed.pb \
	        --mode hierarchy -p 8080 &

eval-hier: env
	python evaluate.py \
	        --evalfile pipeline/data/eval_2col.tsv \
	        --outfile results/metrics_hier_k3.csv \
	        --topk 3

figures: eval-hier
	python scripts/make_plots.py

clean:
	rm -rf results/*.csv fig/*.pdf \
	       assets/graphs/osm_edges.json \
	       assets/hierarchies/osm_louvain_gamma*.json

# ── 3 Louvain hierarchy build chain ──────────────────────────────────
GRAPH      := assets/graphs/osm_edges.json
GAMMA      ?= 1.0
HIERARCHY  := assets/hierarchies/osm_louvain_gamma$(GAMMA).json

$(GRAPH): src/RecoSrv/pipeline/build_graph.py  pipeline/data/tags.tsv
	python src/RecoSrv/pipeline/build_graph.py \
	       --in pipeline/data/tags.tsv --out $@

$(HIERARCHY): $(GRAPH) pipeline/build_hierarchy.py
	python pipeline/build_hierarchy.py \
	       --graph $(GRAPH) --out $@ --gamma $(GAMMA)

build-graph:       $(GRAPH)
build-hierarchy:   $(HIERARCHY)

# ── 4 Quick 300-row evaluation ───────────────────────────────────────
EVAL_BIG   := pipeline/data/eval_2col.tsv
EVAL_SMALL := pipeline/data/eval_min.tsv

$(EVAL_SMALL): $(EVAL_BIG) pipeline/filter_eval.py
	python pipeline/filter_eval.py $< $@ -n 300

evaluate-small: $(EVAL_SMALL) env
	$(MAKE) -C src/RecoSrv evaluate EVALFILE=../../$(EVAL_SMALL)
