package schematree

import "sort"

// helper: geometric decay with depth
func weight(depth int) float64 {
    if depth < 1 {
        depth = 1
    }
    return 1.0 / float64(depth) // depth-1 → 1.0, depth-2 → 0.5
}


// RecommendFromHierarchy returns up to k sibling / cousin tags.
func (h *Hierarchy) RecommendFromHierarchy(input []string, k int) []RankedPropertyCandidate {
    if len(h.tagToParent) == 0 {
        return nil // hierarchy not loaded
    }

    candidates := map[string]float64{}

    for _, tag := range input {
        parent := h.tagToParent[tag]

        // Fallback: boost global-freq tags when tag not in hierarchy
        if parent == nil {
           for _, freqTag := range h.globalTopN {
            candidates[freqTag] += 0.1
            }
           continue
        }
    
        // siblings (depth-1)
        for _, sib := range parent.Tags {
            if sib != tag {
                candidates[sib] += weight(1)
            }
        }
        // cousins (depth-2)
        for _, c := range parent.Children {
            for _, ct := range c.Tags {
                if ct != tag {
                    candidates[ct] += weight(2)
                }
            }
        }
    }

    // convert to slice
    out := make(PropertyRecommendations, 0, len(candidates))
    for t, sc := range candidates {
        tCopy := t
        itm := &IItem{Str: &tCopy}
        out = append(out, RankedPropertyCandidate{Property: itm, Probability: sc})
    }

    // sort by score
    sort.Slice(out, func(i, j int) bool { return out[i].Probability > out[j].Probability })

    if k > 0 && len(out) > k {
        out = out[:k]
    }
    return out
}