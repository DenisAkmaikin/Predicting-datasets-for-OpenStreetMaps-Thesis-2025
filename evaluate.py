#!/usr/bin/env python3
"""
Generic evaluation script for RecommenderServer.

* prec  hit-rate (prec1, precK)
* map    mean average precision@K  (mapK)
* ndcg   normalised DCG@K          (ndcgK)
"""

from __future__ import annotations
import argparse, csv, math, pathlib, sys, time
from typing import Dict, List, Sequence, Tuple
import requests


#CLI
parser = argparse.ArgumentParser(description="Evaluate RecommenderServer")
parser.add_argument("--outfile",  required=True,
                    help="CSV file to write the results into")
parser.add_argument("--evalfile", default="pipeline/data/eval.tsv",
                    help="TSV file with query│gold columns")
parser.add_argument("--topk",    type=int, default=3,
                    help="K for all@K metrics (default 3)")
parser.add_argument("--metric",
                    choices=["prec", "map", "ndcg"], default="prec",
                    help="Metric to compute (prec, map, ndcg)")
parser.add_argument("--server",
                    default="http://localhost:8080/recommender",
                    help="RecoSrv endpoint (default :8080)")
parser.add_argument("--pause",   type=float, default=0.0, metavar="SEC",
                    help="Sleep after every request (throttle)")
parser.add_argument("--slices",  action="store_true",
                    help="Write per-slice CSVs (building/…)")
args = parser.parse_args()


# helpers
def parse_line(line: str) -> Tuple[List[str], List[str]]:
    """Return (query_tags, gold_tags). Expects one TAB."""
    if line.count("\t") != 1:
        raise ValueError(f"Bad line (need exactly one TAB): {line!r}")
    query_str, gold_str = line.split("\t")
    q = [t.strip() for t in query_str.replace(",", ";").split(";") if t.strip()]
    g = [t.strip() for t in gold_str.replace(",", ";").split(";") if t.strip()]
    return q, g


def call_server(tags: Sequence[str]) -> List[str]:
    body = {"properties": list(tags)}
    r    = requests.post(args.server, json=body, timeout=10)
    r.raise_for_status()
    return [rec["property"] for rec in r.json()["recommendations"]]


def precision_hits(recs: Sequence[str], gold: set[str]) -> Tuple[int, int]:
    hit1 = int(bool(recs) and recs[0] in gold)
    hitk = int(any(tag in gold for tag in recs[: args.topk]))
    return hit1, hitk


def average_precision_at_k(recs: Sequence[str], gold: set[str]) -> float:
    score, hits = 0.0, 0
    for i, tag in enumerate(recs[: args.topk], 1):
        if tag in gold:
            hits += 1
            score += hits / i
    denom = min(len(gold), args.topk)
    return score / denom if denom else 0.0


def ndcg_at_k(recs: Sequence[str], gold: set[str]) -> float:
    dcg = 0.0
    for i, tag in enumerate(recs[: args.topk], 1):
        if tag in gold:
            dcg += 1 / math.log2(i + 1)
    ideal = min(len(gold), args.topk)
    idcg  = sum(1 / math.log2(i + 1) for i in range(1, ideal + 1)) or 1.0
    return dcg / idcg


def mrr_at_k(recs: Sequence[str], gold: set[str]) -> float:
    for i, tag in enumerate(recs[: args.topk], 1):
        if tag in gold:
            return 1 / i
    return 0.0


def category_of(query: List[str]) -> str:
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

#main
eval_lines  = pathlib.Path(args.evalfile).read_text().splitlines()
metrics: List[Dict[str, float]]             = []
per_slice: Dict[str, List[Dict[str, float]]] = {}

t0 = time.time()
for idx, line in enumerate(eval_lines, 1):
    if not line.strip():
        continue

    query, gold = parse_line(line)
    gold_set    = set(gold)

    try:
        recs = call_server(query)
    except Exception as exc:
        print(f"[WARN] line {idx}: {exc}", file=sys.stderr)
        recs = []

    row: Dict[str, float] = {}

    if args.metric == "prec":
        hit1, hitk = precision_hits(recs, gold_set)
        row["prec1"]         = hit1
        row[f"prec{args.topk}"] = hitk
    elif args.metric == "map":
        row[f"map{args.topk}"] = average_precision_at_k(recs, gold_set)
    else:   # ndcg
        row[f"ndcg{args.topk}"] = ndcg_at_k(recs, gold_set)

    row["mrr"]  = mrr_at_k(recs, gold_set)      # always add MRR
    row["slice"] = category_of(query)

    metrics.append(row)
    per_slice.setdefault(row["slice"], []).append(row)

    if args.pause > 0:
        time.sleep(args.pause)

print(f"Evaluated {len(metrics)} rows in {time.time() - t0:.1f} s")

#main csv
csv_path = pathlib.Path(args.outfile)
with csv_path.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=metrics[0].keys())
    w.writeheader()
    w.writerows(metrics)
print(f" wrote {csv_path}  ({len(metrics)} rows)")

# write csv slice
if args.slices:
    for sl, rows in per_slice.items():
        p = csv_path.with_stem(csv_path.stem + f"_{sl}")
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"   {sl}: {len(rows)} rows {p.name}")




