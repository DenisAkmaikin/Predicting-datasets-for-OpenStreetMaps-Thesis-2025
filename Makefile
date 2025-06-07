# -------------------- project-wide Makefile --------------------
.PHONY: env install serve-hier eval-hier figures clean \
        build-hierarchy evaluate-small

env: install                     # alias target

install:
        conda env create -f environment.yml --name reco-thesis || true

serve-hier:
        ./RecoSrv serve pipeline/data/tags.tsv.schemaTree.typed.pb \
                --mode hierarchy -p 8080 &

eval-hier:
        python evaluate.py \
                --evalfile pipeline/data/eval_2col.tsv \
                --outfile results/metrics_hier_k3.csv \
                --topk 3

figures: eval-hier
        python scripts/make_plots.py

clean:
        rm -rf results/*.csv fig/*.pdf

# ---------------------------------------------------------------
# Louvain hierarchy builder (γ is overridable):
HIERARCHY = assets/hierarchies/osm_louvain_gamma$(GAMMA).json

$(HIERARCHY): assets/graphs/osm_edges.json pipeline/build_hierarchy.py
        python pipeline/build_hierarchy.py --edges $< --tree $@ --gamma $(GAMMA)

build-hierarchy: $(HIERARCHY)
        @echo "✓ hierarchy written to $(HIERARCHY)"

# ---------------------------------------------------------------
# Quick 300-row evaluation
EVAL_BIG   = pipeline/data/eval_2col.tsv
EVAL_SMALL = pipeline/data/eval_min.tsv

$(EVAL_SMALL): $(EVAL_BIG) pipeline/filter_eval.py
        python pipeline/filter_eval.py $< $@ -n 300

evaluate-small: $(EVAL_SMALL) env
        $(MAKE) -C src/RecoSrv evaluate EVALFILE=../../$(EVAL_SMALL)
