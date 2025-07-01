#!/usr/bin/env python3
"""
Generate a balanced 3 200-row benchmark from the Dutch extract.
"""

import gzip, json, random, pathlib, collections

SRC   = "assets/osm_tags.json.gz"
DEST  = "pipeline/data/eval_balanced.tsv"
ROWS_PER_SLICE = 400
random.seed(42)

# helpers
def tag_dict(obj):
    props = obj.get("properties", {})
    if isinstance(props.get("tags"), dict):        
        return props["tags"]
    return props if isinstance(props, dict) else {}  

def slice_of(kvs):
    for kv in kvs:
        if kv.startswith("building="):  return "building"
        if kv.startswith("highway="):   return "highway"
        if kv.startswith("railway="):   return "railway"
        if kv.startswith("waterway="):  return "waterway"
        if kv.startswith("landuse="):   return "landuse"
        if kv.startswith("natural="):   return "natural"
        if kv.startswith("amenity="):   return "amenity"
    return "misc"

sanitize = lambda s: str(s).replace("\t", " ").replace("\n", " ").replace("\r", " ")

# streaming
buckets = collections.defaultdict(list)
scanned = 0

with gzip.open(SRC, "rt", encoding="utf-8", errors="ignore") as fh:
    for ln in fh:
        if ln and ln[0] == '\x1e':
            ln = ln[1:]
        tags_raw = tag_dict(json.loads(ln))
        if len(tags_raw) < 3:
            continue

        tags = {k: sanitize(v) for k, v in tags_raw.items()}
        kvs  = [f"{k}={v}" for k, v in tags.items()]
        if len(kvs) < 2:
            continue

        sl = slice_of(kvs)
        if len(buckets[sl]) >= ROWS_PER_SLICE:
            continue

        random.shuffle(kvs)
        query, gold = ";".join(kvs[:-1]), kvs[-1]
        buckets[sl].append(f"{query}\t{gold}")

        if len(buckets) == 8 and all(len(v) >= ROWS_PER_SLICE for v in buckets.values()):
            break
        scanned += 1

# writing
rows = sum(buckets.values(), [])
random.shuffle(rows)
pathlib.Path(DEST).parent.mkdir(parents=True, exist_ok=True)
pathlib.Path(DEST).write_text("\n".join(rows) + "\n")
print(f"wrote {len(rows)} rows (scanned {scanned:,} objects) to {DEST}")


