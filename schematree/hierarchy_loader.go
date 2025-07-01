package schematree

import (
	"encoding/json"
	"os"
	"sort"
)

// Tree JSON structs
type TreeNode struct {
	Name     string      `json:"name"`
	Tags     []string    `json:"tags,omitempty"`
	Children []*TreeNode `json:"children,omitempty"`
}

// Hierarchy: roots + look-ups
type Hierarchy struct {
	Roots        []*TreeNode
	tagToParent  map[string]*TreeNode // leaf tag = parent node
	globalTopN   []string             // most-frequent tags 
}

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

	h := &Hierarchy{
		Roots:       roots,
		tagToParent: map[string]*TreeNode{},
	}
	freq := map[string]int{}

	h.indexTags(nil, roots, freq)

	// build globalTopN = 200 most-frequent tags
	type kv struct{ tag string; cnt int }
	tmp := make([]kv, 0, len(freq))
	for t, c := range freq {
		tmp = append(tmp, kv{t, c})
	}
	sort.Slice(tmp, func(i, j int) bool { return tmp[i].cnt > tmp[j].cnt })

	N := 200
	if len(tmp) < N {
		N = len(tmp)
	}
	h.globalTopN = make([]string, N)
	for i := 0; i < N; i++ {
		h.globalTopN[i] = tmp[i].tag
	}
	return h, nil
}

// indexTags fills tagToParent and tallies frequencies recursively.
func (h *Hierarchy) indexTags(parent *TreeNode, nodes []*TreeNode, freq map[string]int) {
	for _, n := range nodes {
		if len(n.Tags) > 0 {
			for _, t := range n.Tags {
				h.tagToParent[t] = parent
				freq[t]++
			}
		}
		if len(n.Children) > 0 {
			h.indexTags(n, n.Children, freq)
		}
	}
}


