import json, random
from wordcloud import WordCloud
import matplotlib.pyplot as plt

with open("assets/hierarchies/osm_louvain_gamma2.0.json") as f:
    data = json.load(f)
leaf_clusters = []
def collect_leaves(nodes):
    for node in nodes:
        if "tags" in node:
            leaf_clusters.append(node["tags"])
        elif "children" in node:
            collect_leaves(node["children"])

collect_leaves(data)

cluster = random.choice([tags for tags in leaf_clusters if len(tags) > 5])

# Word cloud
text = " ".join(cluster)
wc = WordCloud(width=1200, height=600, background_color="white").generate(text)
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.show()

