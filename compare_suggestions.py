#!/usr/bin/env python3
# compare_suggestions.py
#
# Show top-N recommendations from the hierarchy server (8080) and the
# flat-frequency baseline (8081) for a given context tag list.
#
# Usage examples
# --------------
#  1) Pick a random row from the BALANCED benchmark:
#       python compare_suggestions.py --sample pipeline/data/eval_balanced.tsv
#
#  2) Supply your own context:
#       python compare_suggestions.py \
#              --tags "waterway=canal;boat=yes;bridge=yes" --top 10
#
#  3) Compare a particular TSV line number (1-based):
#       python compare_suggestions.py --line 137  pipeline/data/eval_complex.tsv
#
# Both servers must already be running:
#   ./RecoSrv serve ... --mode hierarchy -p 8080 &
#   ./RecoSrv serve ... --mode flat       -p 8081 &
#
import argparse, pathlib, random, requests, textwrap, sys

def call(server_url, tags, n):
    r = requests.post(
        f"{server_url}/recommender",
        json={"properties": tags},
        timeout=5
    )
    r.raise_for_status()
    return [rec["property"] for rec in r.json()["recommendations"][:n]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="?", help="evaluation TSV file (optional)")
    ap.add_argument("--sample", action="store_true",
                    help="pick a random row from the TSV")
    ap.add_argument("--line", type=int, metavar="N",
                    help="use line N (1-based) from the TSV")
    ap.add_argument("--tags", help="semicolon-separated tag list to use instead")
    ap.add_argument("--top", type=int, default=10, help="top-N to display")
    args = ap.parse_args()

    if args.tags:
        context = [t.strip() for t in args.tags.split(";") if t.strip()]
    elif args.tsv:
        rows = pathlib.Path(args.tsv).read_text().splitlines()
        if args.sample:
            row = random.choice(rows)
        elif args.line:
            if args.line < 1 or args.line > len(rows):
                sys.exit(f"Line {args.line} out of range (1..{len(rows)})")
            row = rows[args.line-1]
        else:
            sys.exit("Need --sample or --line when TSV is given.")
        context = row.split("\t")[0].split(";")
    else:
        ap.print_help(); sys.exit(1)

    print("\nContext tags:")
    for t in context:
        print(f"  • {t}")
    print()

    hier = call("http://localhost:8080", context, args.top)
    flat = call("http://localhost:8081", context, args.top)

    width = max(len(t) for t in hier+flat) + 2
    print(f"{'Rank':<4} {'Hierarchy':<{width}} Flat baseline")
    print("-" * (8 + 2*width))
    for i in range(args.top):
        h = hier[i] if i < len(hier) else ""
        f = flat[i] if i < len(flat) else ""
        mark = "<" if h == f else ""
        print(f"{i+1:>2}.  {h:<{width}} {f} {mark}")

if __name__ == "__main__":
    main()
