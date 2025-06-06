#!/usr/bin/env python3
"""
Build a recursive Louvain hierarchy from an edge list.

✔ stops if Louvain returns only 1 community
✔ stops if depth == max_depth
"""

import argparse, json, os, networkx as nx
from collections import defaultdict
from community import best_partition   # package: python-louvain


# ---------- CLI ----------
def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--edges", required=True)
    p.add_argument("--tree",  required=True)
    p.add_argument("--max_leaf",  type=int, default=4000,
                   help="do not split communities smaller than this")
    p.add_argument("--max_depth", type=int, default=6,
                   help="stop recursion after this depth")
    return p.parse_args()


# ---------- helpers ----------
def load_graph(path):
    G = nx.Graph()
    with open(path) as fh:
        for e in json.load(fh):
            G.add_edge(e["source"], e["target"], weight=e["weight"])
    return G


def recursive_louvain(G, max_leaf, depth, max_depth):
    """
    Returns a list of tree nodes:
      { "name": "C42", "tags":[…] }          leaf
      { "name": "C7",  "children":[…] }      internal
    """
    # base-cases ----------------------------------------------------------
    if depth >= max_depth or len(G) <= max_leaf:
        return [{"name": f"L{depth}", "tags": list(G.nodes)}]

    part = best_partition(G, weight="weight")
    # if Louvain produced only ONE community, stop here
    if len(set(part.values())) == 1:
        return [{"name": f"L{depth}", "tags": list(G.nodes)}]
    # --------------------------------------------------------------------

    comm2nodes = defaultdict(list)
    for node, cid in part.items():
        comm2nodes[cid].append(node)

    tree = []
    for cid, nodes in comm2nodes.items():
        sub = G.subgraph(nodes)
        subtree = recursive_louvain(
            sub, max_leaf,
            depth + 1, max_depth
        )
        tree.append(
            {"name": f"depth{depth}_C{cid}",
             "children": subtree} if "children" in subtree[0]
             else {"name": f"depth{depth}_C{cid}",
                   "tags": subtree[0]["tags"]}
        )
    return tree


# ---------- main ----------
def main():
    a = parse()
    G = load_graph(a.edges)
    print("graph:", G.number_of_nodes(), "nodes", G.number_of_edges(), "edges")

    tree = recursive_louvain(G, a.max_leaf, depth=0, max_depth=a.max_depth)

    os.makedirs(os.path.dirname(a.tree), exist_ok=True)
    with open(a.tree, "w") as fh:
        json.dump(tree, fh)
    print("hierarchy saved →", a.tree)


if __name__ == "__main__":
    main()

