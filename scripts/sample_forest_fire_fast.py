#!/usr/bin/env python3
"""
Fast forest-fire edge sampler 
Keeps roughly --target fraction of edges with forward burn probabibility --p.
"""

from __future__ import annotations
import argparse, ijson, json, random, time, pathlib, sys, collections

ap = argparse.ArgumentParser()
ap.add_argument("--src",   required=True)
ap.add_argument("--dest",  required=True)
ap.add_argument("--p",     type=float, default=0.3)   # forward probability
ap.add_argument("--target",type=float, default=0.1)   # keep ~10 %
ap.add_argument("--queue", type=int,   default=100_000,
                help="max burn-queue size (default 100 k)")
args = ap.parse_args()

src  = pathlib.Path(args.src)
dest = pathlib.Path(args.dest).open("w")
random.seed(42)

burn  = collections.deque(maxlen=args.queue)  # recent burnt nodes
kept  = 0
t0    = time.time()

try:
    with src.open("rb") as f:
        for i, edge in enumerate(ijson.items(f, "item"), 1):
            src_v, dst_v = edge["source"], edge["target"]

            if (src_v in burn) or (dst_v in burn):
                if random.random() < args.p:
                    json.dump(edge, dest); dest.write("\n")
                    kept += 1
                    burn.append(src_v); burn.append(dst_v)

            # initialise fires sparsely until we hit the target ratio
            elif kept < args.target * (i+1) and random.random() < 0.002:
                burn.append(src_v); burn.append(dst_v)

            if i % 5_000_000 == 0:
                sys.stderr.write(f"\r{kept:,} edges kept after {i:,}")
                sys.stderr.flush()
except KeyboardInterrupt: 
    print("Interrupted" )

dest.close()
print(f"\nwrote {kept:,} edges  to  {args.dest}   "
      f"({kept/i:.3%} of {i:,}) in {time.time()-t0:.1f}s")


