#!/usr/bin/env python3
"""
Generic evaluation script for RecommenderServer.

Columns in the evaluation file (TAB-separated)
----------------------------------------------
col-0 : query tags   (comma **or** semicolon separated)
col-1 : gold  tags   (comma | semicolon separated)

Metrics written to the output CSV
---------------------------------
prec1      – hit@1
precK      – hit@K              (K = --topk, default 3)
mapK       – mean-average-precision@K (if --metric map is chosen)
slice      – optional category label per test case

Typical usage
-------------
# hierarchy mode, default metrics
./RecoSrv serve … --mode hierarchy -p 8080 &
python evaluate.py --outfile metrics_h.csv

# flat tree, MAP@10, per-category CSVs, gentle throttling
./RecoSrv serve … --mode tree -p 8080 &
python evaluate.py --metric map --topk 10 --pause 0.05 --slices \
                   --outfile metrics_t.csv
"""

from __future__ import annotations

import argparse, csv, pathlib, statistics, sys, time
from typing import Dict, List, Sequence, Tuple

import requests


# ────────────────────────────── CLI ────────────────────────────────
parser = argparse.ArgumentParser(description="Evaluate RecommenderServer")
parser.add_argument("--outfile",  required=True,
                    help="CSV file to write the results into")
parser.add_argument("--evalfile", default="pipeline/data/eval.tsv",
                    help="TAB-separated file with query│gold columns")
parser.add_argument("--topk",    type=int, default=3,
                    help="Compute precision / MAP at K (default 3)")
parser.add_argument("--metric",  choices=["prec", "map"], default="prec",
                    help="Which metric to compute (prec or map, default prec)")
parser.add_argument("--server",  default="http://localhost:8080/recommender",
                    help="Running RecoSrv endpoint (default localhost:8080)")
parser.add_argument("--pause",   type=float, default=0.0, metavar="SEC",
                    help="Seconds to sleep **after every request** "
                         "(e.g. 0.05 → 50 ms; throttles the load)")
parser.add_argument("--slices",  action="store_true",
                    help="Write one extra CSV per tag family (building/…)")
args = parser.parse_args()


# ───────────────────────── helper utils ────────────────────────────
def parse_line(line: str) -> Tuple[List[str], List[str]]:
    """Return (query_tags, gold_tags).  Expects exactly **one** TAB."""
    try:
        query_str, gold_str = line.split("\t")
    except ValueError:
        raise ValueError(f"Bad line (need exactly one TAB): {line!r}")

    q = [t.strip() for t in query_str.replace(",", ";").split(";") if t.strip()]
    g = [t.strip() for t in gold_str.replace(",", ";").split(";") if t.strip()]
    return q, g


def call_server(tags: Sequence[str]) -> List[str]:
    """Return the list of recommended tag strings."""
    body = {"properties": list(tags)}
    r    = requests.post(args.server, json=body, timeout=10)
    r.raise_for_status()
    return [rec["property"] for rec in r.json()["recommendations"]]


def precision_hits(recs: Sequence[str], gold: set[str]) -> Tuple[int, int]:
    """Return (hit@1, hit@K)."""
    hit1 = int(bool(recs) and recs[0] in gold)
    hitk = int(any(tag in gold for tag in recs[: args.topk]))
    return hit1, hitk


def average_precision_at_k(recs: Sequence[str], gold: set[str]) -> float:
    """
    AP@K = Σ_i ( Prec@i * rel_i ) / min(|gold|, K)
    where rel_i = 1 if recs[i] ∈ gold else 0
    """
    score, hits = 0.0, 0
    for i, tag in enumerate(recs[: args.topk], start=1):
        if tag in gold:
            hits  += 1
            score += hits / i          # precision@i
    denom = min(len(gold), args.topk)
    return score / denom if denom else 0.0


def category_of(query: List[str]) -> str:
    """Crude slice label based on the first tag in the query."""
    if not query:
        return "misc"
    prefix = query[0].split("=", 1)[0]
    return {
        "building":  "building",
        "highway":   "highway",
        "railway":   "railway",
        "waterway":  "waterway",
        "addr:city": "address",
    }.get(prefix, "misc")


# ───────────────────────── main loop ───────────────────────────────
eval_lines  = pathlib.Path(args.evalfile).read_text().splitlines()
metrics: List[Dict[str, float]]       = []
per_slice: Dict[str, List[Dict[str,float]]] = {}

t0 = time.time()
for lineno, line in enumerate(eval_lines, start=1):
    if not line.strip():
        continue

    query, gold = parse_line(line)
    gold_set    = set(gold)

    try:
        recs = call_server(query)
    except Exception as exc:
        print(f"[WARN] Line {lineno}: request failed → {exc}", file=sys.stderr)
        recs = []

    row: Dict[str, float] = {}
    if args.metric == "prec":
        hit1, hitk      = precision_hits(recs, gold_set)
        row["prec1"]    = hit1
        row[f"prec{args.topk}"] = hitk
    else:  # MAP
        row[f"map{args.topk}"] = average_precision_at_k(recs, gold_set)

    row["slice"] = category_of(query)
    metrics.append(row)
    per_slice.setdefault(row["slice"], []).append(row)

    # optional throttling
    if args.pause > 0:
        time.sleep(args.pause)

print(f"Evaluated {len(metrics)} rows in {time.time() - t0:.1f} s")

# ─────────────────────── write main CSV ────────────────────────────
csv_path = pathlib.Path(args.outfile)
with csv_path.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=metrics[0].keys())
    w.writeheader(); w.writerows(metrics)
print(f"✓ wrote {csv_path} ({len(metrics)} rows)")

# ─────────────────────── write slice CSVs ──────────────────────────
if args.slices:
    for sl, rows in per_slice.items():
        p = csv_path.with_stem(csv_path.stem + f"_{sl}")
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        print(f"  ↳ {sl}: {len(rows)} rows → {p.name}")

