package schematree

import "sort" 

// RecommendFromHierarchy returns up to k sibling / cousin tags.
func (h *Hierarchy) RecommendFromHierarchy(input []string, k int) []RankedPropertyCandidate {
	if len(h.tagToParent) == 0 {
		return nil // hierarchy not loaded
	}

	seen := map[string]bool{}
	candidates := map[string]int{} // tag → score

	for _, tag := range input {
		parent := h.tagToParent[tag]
		if parent == nil {
			continue // tag not in hierarchy
		}
		// siblings
		for _, sib := range parent.Tags {
			if sib != tag {
				candidates[sib]++
			}
		}
		// cousins (tags in sibling clusters)
		for _, cousinCluster := range parent.Children {
			for _, ct := range cousinCluster.Tags {
				if ct != tag {
					candidates[ct]++
				}
			}
		}
		seen[tag] = true
	}

	 // convert to ranked slice
	 out := make(PropertyRecommendations, 0, len(candidates))
	 for tag, score := range candidates {
 
		 // Wrap tag into a minimal IItem
		 t := tag                      // local copy so &t is addressable
		 itm := &IItem{Str: &t}
 
		 out = append(out, RankedPropertyCandidate{
			 Property:    itm,
			 Probability: float64(score),
		 })
	 }
 
	 // sort descending by probability
	 sort.Slice(out, func(i, j int) bool { return out[i].Probability > out[j].Probability })
	return out
}
