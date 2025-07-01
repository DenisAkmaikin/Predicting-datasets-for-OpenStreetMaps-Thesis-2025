import json, requests, pandas as pd
from collections import defaultdict

EVAL_FILE = "pipeline/data/eval_balanced.tsv"
SERVER    = "http://localhost:8080/recommender"
N = 3  # top-N tags

def tag_key(tag): return tag.split("=", 1)[0]

rows = []
for line in open(EVAL_FILE):
    if "\t" not in line: continue
    q, gold = line.strip().split("\t")
    query = q.split(";")
    resp = requests.post(SERVER, json={"properties": query}, timeout=5)
    recs = [r["property"] for r in resp.json()["recommendations"]][:N]

    query_keys = set(map(tag_key, query))
    match = sum(tag_key(r) in query_keys for r in recs)
    coherence = match / N
    rows.append(coherence)

print("Avg semantic coherence (key overlap with input):", sum(rows)/len(rows))     