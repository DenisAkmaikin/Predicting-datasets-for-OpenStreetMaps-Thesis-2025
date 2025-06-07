#!/usr/bin/env python3
from __future__ import annotations 
"""
Randomly down-sample a tab-separated evaluation file.

Example:
    python pipeline/filter_eval.py  pipeline/data/eval_2col.tsv \
                                    pipeline/data/eval_min.tsv \
                                    -n 300 --seed 123
"""

import argparse, pathlib, random, sys

parser = argparse.ArgumentParser()
parser.add_argument("infile",  help="Original 2-column TSV")
parser.add_argument("outfile", help="Path for the smaller sample")
parser.add_argument("-n", "--num",  type=int, default=200,
                    help="Number of lines to sample (default: 200)")
parser.add_argument("--seed", type=int, default=42,
                    help="Random seed for reproducibility")
args = parser.parse_args()

in_path  = pathlib.Path(args.infile)
out_path = pathlib.Path(args.outfile)
#!/usr/bin/env python3
"""
Randomly down-sample a tab-separated evaluation file.

Example:
    python pipeline/filter_eval.py  pipeline/data/eval_2col.tsv \
                                    pipeline/data/eval_min.tsv \
                                    -n 300 --seed 123
"""

from __future__ import annotations
import argparse, pathlib, random, sys

parser = argparse.ArgumentParser()
parser.add_argument("infile",  help="Original 2-column TSV")
parser.add_argument("outfile", help="Path for the smaller sample")
parser.add_argument("-n", "--num",  type=int, default=200,
                    help="Number of lines to sample (default: 200)")
parser.add_argument("--seed", type=int, default=42,
                    help="Random seed for reproducibility")
args = parser.parse_args()

in_path  = pathlib.Path(args.infile)
out_path = pathlib.Path(args.outfile)

if not in_path.exists():
    sys.exit(f"✗ input file not found: {in_path}")

lines = in_path.read_text().splitlines()
random.seed(args.seed)
sample = random.sample(lines, min(args.num, len(lines)))

out_path.write_text("\n".join(sample) + "\n")
print(f"✓ wrote {len(sample)} lines → {out_path}")
