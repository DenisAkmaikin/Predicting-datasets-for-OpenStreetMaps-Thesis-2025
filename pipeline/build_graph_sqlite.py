#!/usr/bin/env python3
"""
Low-RAM edge builder: counts tag-pairs in an on-disk SQLite DB, then
writes edges ≥ --min_count to JSON. 100 k+ pairs even on a laptop.
"""

import argparse, gzip, itertools, json, os, sqlite3, sys
from pathlib import Path

# CLI
p = argparse.ArgumentParser()
p.add_argument("--tags",   required=True, help="*.json or *.json.gz")
p.add_argument("--edges",  required=True, help="output edge list JSON")
p.add_argument("--min_count", type=int, default=1)
p.add_argument("--temp_db", default="edgecount.db", help="SQLite file")
args = p.parse_args()

# Sqlite 
db = sqlite3.connect(args.temp_db)
db.executescript("""
PRAGMA journal_mode = OFF;
PRAGMA synchronous  = OFF;
PRAGMA temp_store   = MEMORY;
CREATE TABLE IF NOT EXISTS cnt (
  a TEXT, b TEXT, c INTEGER,
  PRIMARY KEY (a,b)
) WITHOUT ROWID;
""")
txn = db.cursor()

# HELPERS
def opener(path):
    return gzip.open(path, "rt", encoding="utf-8", errors="ignore") \
           if path.endswith(".gz") else open(path, "r", encoding="utf-8", errors="ignore")

def tag_pairs(tag_dict):
    tags = [f"{k}={v}" for k,v in tag_dict.items()]
    tags.sort()
    return itertools.combinations(tags, 2)

def extract_tag_dict(obj):
    props = obj.get("properties", {})
    if isinstance(props.get("tags"), dict):
        return props["tags"]
    return props if isinstance(props, dict) else {}

# MAIN LOOP
BATCH = 10_000
count = 0
with opener(args.tags) as fh:
    for i, raw in enumerate(fh, 1):
        if raw and raw[0] == '\x1e': raw = raw[1:]
        try:
            tag_dict = extract_tag_dict(json.loads(raw))
        except json.JSONDecodeError:
            continue
        if len(tag_dict) < 2:
            continue

        for a,b in tag_pairs(tag_dict):
            txn.execute(
                "INSERT INTO cnt VALUES (?,?,1) "
                "ON CONFLICT(a,b) DO UPDATE SET c = c+1", (a,b)
            )
        if i % BATCH == 0:
            db.commit()
            print(f"\rprocessed {i:,}", end="", file=sys.stderr)
    db.commit()
print(f"\r finished {locals().get('i', 0):,} objects")


# Dump edges >= min count
from pathlib import Path

# make sure target directory exists
Path(os.path.dirname(args.edges)).mkdir(parents=True, exist_ok=True)

with open(args.edges, "w") as fout:
    fout.write("[\n")
    first = True

    cursor = db.execute(
        "SELECT a, b, c FROM cnt WHERE c >= ?", (args.min_count,)
    )

    for a, b, w in cursor:
        if not first:
            fout.write(",\n")
        json.dump({"source": a, "target": b, "weight": w}, fout)
        first = False

    fout.write("\n]\n")

print("wrote", args.edges, "with streaming JSON")  #confirmation
