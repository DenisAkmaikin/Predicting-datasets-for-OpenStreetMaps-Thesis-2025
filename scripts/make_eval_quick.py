#!/usr/bin/env python3
import gzip, json, random, pathlib, sys
SRC   = "assets/osm_tags.json.gz"
DEST  = "pipeline/data/eval_complex.tsv"
KEEP  = 300
random.seed(42)

rows, scanned = [], 0
with gzip.open(SRC, "rt", encoding="utf-8", errors="ignore") as fh:
    for ln in fh:
        if ln and ln[0] == '\x1e':
            ln = ln[1:]
        tags = json.loads(ln).get("properties", {}).get("tags", {})
        if len(tags) < 3:
            continue
        t = [f"{k}={v}" for k, v in tags.items()]
        random.shuffle(t)
        rows.append(";".join(t[:-1]) + "\t" + t[-1])
        if len(rows) >= KEEP:
            break
        scanned += 1

pathlib.Path(DEST).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(DEST).write_text("\n".join(rows) + "\n")
print(f"wrote {len(rows)} rows after scanning {scanned:,} objects to{DEST}")

