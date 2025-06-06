.PHONY: install serve-hier eval-hier figures clean

install:
	conda env create -f environment.yml --name reco-thesis

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
