# ---------------- wrapper -----------------
SUBDIR := src/RecoSrv
.PHONY: env evaluate clean

env:
	$$(MAKE) -C $(SUBDIR) env

evaluate: env
	$$(MAKE) -C $(SUBDIR) evaluate

clean:
	$$(MAKE) -C $(SUBDIR) clean
