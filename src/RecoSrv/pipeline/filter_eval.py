#!/usr/bin/env python3
from __future__ import annotations         # must be FIRST

"""
Down-sample an evaluation TSV file to *n* lines.

Example
-------
python pipeline/filter_eval.py  pipeline/data/eval_2col.tsv \
                                pipeline/data/eval_min.tsv   \
                                -n 300 --seed 123
"""
import argparse, pathlib, random, sys

def read_lines(path: pathlib.Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]

def main(inp: str, out: str, n: int, seed: int):
    rnd = random.Random(seed)
    lines = read_lines(pathlib.Path(inp))
    if n > len(lines):
        sys.exit(f"Requested {n} > available {len(lines)} lines")
    sample = rnd.sample(lines, n)

    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(sample) + "\n")
    print(f"✓ wrote {out}  ({n} rows)")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("inp")
    p.add_argument("out")
    p.add_argument("-n", "--n", type=int, default=300)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    main(args.inp, args.out, args.n, args.seed)
