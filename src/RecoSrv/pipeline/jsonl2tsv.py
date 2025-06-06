import json, pathlib, csv, sys

jl  = pathlib.Path("pipeline/data/tags.jsonl")
tsv = pathlib.Path("pipeline/data/tags.tsv")

with jl.open("r", encoding="utf-8", errors="ignore") as f_in, \
     tsv.open("w", newline="", encoding="utf-8") as f_out:

    w = csv.writer(f_out, delimiter="\t")

    for line in f_in:
        # strip JSON-Sequence record separator (0x1E) if present
        if line and line[0] == '\x1e':
            line = line[1:]

        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue

        props = d.get("tags") or d.get("properties", {})
        if len(props) > 1:
            w.writerow([f"{k}={v}" for k, v in props.items()])


