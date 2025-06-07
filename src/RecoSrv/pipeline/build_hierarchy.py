#!/usr/bin/env python3
"""
Build a recursive Louvain hierarchy from an edge-list JSON.

Stops recursion when:
  • Louvain returns only one community, or
  • `depth` reaches `--max_depth`, or
  • community size ≤ `--max_leaf`
"""

from __future__ import annotations
import argparse, json, os
from collections import defaultdict

import networkx as nx
from community import community_louvain   # pip install python-louvain

# CLI
p = argparse.ArgumentParser()
p.add_argument("--edges",  default="assets/graphs/osm_edges.json",
               help="edge list in node-link JSON (source, target, weight)")
p.add_argument("--tree",   default="assets/hierarchies/osm_louvain.json",
               help="output hierarchy JSON")
p.add_argument("--gamma",  type=float, default=1.0,
               help="Louvain resolution parameter (↑ = more communities)")
p.add_argument("--max_leaf",  type=int, default=4000,
               help="don’t split communities smaller than this")
p.add_argument("--max_depth", type=int, default=6,
               help="stop recursion after this depth")
args = p.parse_args()

# Helpers
def load_graph(path: str) -> nx.Graph:
    return nx.readwrite.json_graph.node_link_graph(json.load(open(path)))

def recursive_louvain(G: nx.Graph, depth: int = 0) -> list[dict]:
    """Return a hierarchy subtree (list with one internal or leaf node)."""
    if depth >= args.max_depth or len(G) <= args.max_leaf:
        return [{"name": f"L{depth}", "tags": list(G.nodes)}]

    part = community_louvain.best_partition(G, resolution=args.gamma, weight="weight")
    # If Louvain produced only ONE community, stop here
    if len(set(part.values())) == 1:
        return [{"name": f"L{depth}", "tags": list(G.nodes)}]

    comm2nodes: dict[int, list[str]] = defaultdict(list)
    for node, cid in part.items():
        comm2nodes[cid].append(node)

    children = []
    for cid, nodes in comm2nodes.items():
        sub = G.subgraph(nodes)
        child_subtree = recursive_louvain(sub, depth + 1)
        children.append(
            {"name": f"D{depth}_C{cid}", "children": child_subtree}
        )
    return [{"name": f"L{depth}", "children": children}]

# main
G = load_graph(args.edges)
hierarchy = recursive_louvain(G)

os.makedirs(os.path.dirname(args.tree), exist_ok=True)
with open(args.tree, "w") as fh:
    json.dump(hierarchy[0]["children"], fh)   # drop the artificial root
print(f"✓ hierarchy saved → {args.tree}")
