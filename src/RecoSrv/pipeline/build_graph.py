#!/usr/bin/env python3
import argparse, json, itertools, collections, os, gzip

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--tags", required=True)
    p.add_argument("--edges", required=True)
    p.add_argument("--min_count", type=int, default=2)
    return p.parse_args()

def tag_pairs(tag_dict: dict):
    if len(tag_dict) < 2:
        return
    tags = [f"{k}={v}" for k, v in tag_dict.items()]
    tags.sort()
    for a, b in itertools.combinations(tags, 2):
        yield (a, b)

def extract_tag_dict(obj):
    props = obj.get("properties", {})
    # case 1: tags nested in properties["tags"]
    if "tags" in props and isinstance(props["tags"], dict):
        return props["tags"]
    # case 2: every key in properties IS a tag
    return props if isinstance(props, dict) else {}

def main():
    a = parse_args()
    counter = collections.Counter()
    examples = 0

    opener = gzip.open if a.tags.endswith(".gz") else open
    with opener(a.tags, "rt", encoding="utf-8", errors="ignore") as fh:
        for i, raw in enumerate(fh, 1):
    # strip the JSON-Sequence record-separator (0x1E) if present
            if raw and raw[0] == '\x1e':
                raw = raw[1:]
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            tag_dict = extract_tag_dict(obj)
            if not tag_dict or len(tag_dict) < 2:
                continue
            examples += 1
            for pair in tag_pairs(tag_dict):
                counter[pair] += 1
            if i % 100_000 == 0:
                print(f"\rprocessed {i:,} objects, with ≥2 tags: {examples:,}", end="")
    print(f"\nunique pairs: {len(counter):,}")

    os.makedirs(os.path.dirname(a.edges), exist_ok=True)
    edges = [ {"source": s, "target": t, "weight": w}
              for (s, t), w in counter.items() if w >= a.min_count ]
    print(f"edges ≥{a.min_count}: {len(edges):,}")
    with open(a.edges, "w", encoding="utf-8") as out:
        json.dump(edges, out)
    print("saved →", a.edges)

if __name__ == "__main__":
    main()
