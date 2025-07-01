#!/usr/bin/env python3
"""
Build a recursive Louvain/Leiden hierarchy from a flat edge JSON.
"""

from __future__ import annotations
import argparse, json, os, random
import ijson
from igraph import Graph
import leidenalg

# CLI
p = argparse.ArgumentParser()
p.add_argument("--edges", default="assets/graphs/osm_edges.json")
p.add_argument("--tree",  default="assets/hierarchies/osm_louvain.json")
p.add_argument("--gamma", type=float, default=1.0)
p.add_argument("--max_leaf",  type=int, default=4000)
p.add_argument("--max_depth", type=int, default=6)
args = p.parse_args()

SAMPLERATE = 10    #can change this parameter for different graph sampling
BATCH      = 1_000_000

def load_graph_ig(path: str) -> Graph:
    random.seed(42)
    id_map, edges, weights = {}, [], []
    G = Graph()
    with open(path, "rb") as f:
        for edge in ijson.items(f, "item"):
            for tag in (edge["source"], edge["target"]):
                if tag not in id_map:
                    id_map[tag] = len(id_map)
                    G.add_vertex()
            if random.randint(1, SAMPLERATE) != 1:
                continue
            edges.append((id_map[edge["source"]], id_map[edge["target"]]))
            weights.append(edge["weight"])
            if len(edges) >= BATCH:
                G.add_edges(edges)
                G.es[-len(edges):]["weight"] = weights
                edges, weights = [], []
    if edges:
        G.add_edges(edges)
        G.es[-len(edges):]["weight"] = weights
    G.vs["tag"] = [None] * G.vcount()
    for tag, vid in id_map.items():
        G.vs[vid]["tag"] = tag
    print(G.summary())
    return G

def recurse(G: Graph, depth=0) -> list[dict]:
    if depth >= args.max_depth or G.vcount() <= args.max_leaf:
        return [{"name": f"L{depth}", "tags": G.vs["tag"]}]
    part = leidenalg.find_partition(
        G,
        leidenalg.RBConfigurationVertexPartition,
        weights="weight",
        resolution_parameter=args.gamma,
    )
    if len(part) == 1:
        return [{"name": f"L{depth}", "tags": G.vs["tag"]}]
    children = []
    for cid, verts in enumerate(part):
        children.append({
            "name": f"D{depth}_C{cid}",
            "children": recurse(G.subgraph(verts), depth + 1),
        })
    return [{"name": f"L{depth}", "children": children}]

G = load_graph_ig(args.edges)
#
low_deg = [v.index for v in G.vs if v.degree() < 3]
G.delete_vertices(low_deg)
print(f"filtered -> V={G.vcount():,}  E={G.ecount():,}")
#
hierarchy = recurse(G)
os.makedirs(os.path.dirname(args.tree), exist_ok=True)
with open(args.tree, "w") as fh:
    json.dump(hierarchy[0]["children"], fh)
print("hierarchy saved to", args.tree)
