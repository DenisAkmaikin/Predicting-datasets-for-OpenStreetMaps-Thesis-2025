#!/usr/bin/env python3
"""
requires ≥3 tags total
Requires ≥2 tags NOT starting with (“building”, “addr:”)
Gold tag is the first acceptable tag after shuffling.
"""

import gzip, json, pathlib, random, sys, itertools

SRC   = "assets/osm_tags.json.gz"
DEST  = "pipeline/data/eval_complex.tsv"
KEEP  = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
random.seed(42)

def tag_dict(obj):
    props = obj.get("properties", {})
    if isinstance(props.get("tags"), dict):
        return props["tags"]
    return props if isinstance(props, dict) else {}

rows, scanned = [], 0
with gzip.open(SRC, "rt", encoding="utf-8", errors="ignore") as fh:
    for ln in fh:
        scanned += 1
        if ln and ln[0] == '\x1e':
            ln = ln[1:]
        tags = tag_dict(json.loads(ln))

        n_non_bld = sum(1 for k in tags if not k.startswith(("building", "addr")))
        if len(tags) < 3 or n_non_bld < 2:    
            continue                            

        t_list = [f"{k}={v}" for k, v in tags.items()]
        random.shuffle(t_list)
        query, gold = t_list[:-1], t_list[-1]
        rows.append(";".join(query) + "\t" + gold)

        if len(rows) >= KEEP:  #check progress
            break
        if scanned % 100_000 == 0:             
            print(f"scanned {scanned:,}; rows {len(rows):,}")

pathlib.Path(DEST).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(DEST).write_text("\n".join(rows) + "\n")
print(f"wrote {DEST} ({len(rows)} rows, scanned {scanned:,} objects)")
