package schematree

import (
	"encoding/json"
	"os"
)

// TreeNode matches the JSON we just wrote
type TreeNode struct {
	Name     string      `json:"name"`
	Tags     []string    `json:"tags,omitempty"`
	Children []*TreeNode `json:"children,omitempty"`
}

// Hierarchy holds root nodes + a tag-to-node lookup
type Hierarchy struct {
	Roots       []*TreeNode
	tagToParent map[string]*TreeNode // leaf tag → parent node
}

// ------------ public API ------------

// LoadHierarchy reads the JSON file and builds fast look-ups.
func LoadHierarchy(path string) (*Hierarchy, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var roots []*TreeNode
	if err := json.NewDecoder(f).Decode(&roots); err != nil {
		return nil, err
	}

	h := &Hierarchy{Roots: roots, tagToParent: map[string]*TreeNode{}}
	h.indexTags(nil, roots)
	return h, nil
}

// indexTags fills tagToParent by walking the tree.
func (h *Hierarchy) indexTags(parent *TreeNode, nodes []*TreeNode) {
	for _, n := range nodes {
		if len(n.Tags) > 0 {
			for _, t := range n.Tags {
				h.tagToParent[t] = parent
			}
		}
		if len(n.Children) > 0 {
			h.indexTags(n, n.Children)
		}
	}
}
