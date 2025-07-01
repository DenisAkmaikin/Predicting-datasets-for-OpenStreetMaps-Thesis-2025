package schematree

import (
	"fmt"
	"sort"
)
var RecoMode = "hierarchy" // default; can be changed by flag

// RankedPropertyCandidate is a struct used to rank suggestions
type RankedPropertyCandidate struct {
	Property    *IItem
	Probability float64
}

// PropertyRecommendations is a slice of RankedPropertyCandidate
type PropertyRecommendations []RankedPropertyCandidate

// String pretty-prints a recommendation list
func (ps PropertyRecommendations) String() string {
	s := ""
	for _, p := range ps {
		s += fmt.Sprintf("%v: %v\n", *p.Property.Str, p.Probability)
	}
	return s
}

// Top10AvgProbibility returns the average probability of the top-10 items
func (ps PropertyRecommendations) Top10AvgProbibility() float32 {
	var sum float64
	for i := 0; i < 10; i++ {
		if i < len(ps) {
			sum += ps[i].Probability
		}
	}
	return float32(sum) / 10.0
}

/* ------------------------------------------------------------------ */
/*  Public entry point                                                 */
/* ------------------------------------------------------------------ */

// Recommend returns a ranked list of property candidates for the input tags.
// It first tries the Louvain hierarchy; if that yields nothing it falls back
// to the original SchemaTree recommender.
func (tree *SchemaTree) Recommend(properties []string, types []string) PropertyRecommendations {

    if RecoMode == "hierarchy" || RecoMode == "hybrid" {
        if tree.Hierarchy != nil {
            hr := tree.Hierarchy.RecommendFromHierarchy(properties, 15)
            if len(hr) > 0 && RecoMode == "hierarchy" {
                return hr
            }
            if len(hr) > 0 && RecoMode == "hybrid" {
                // keep the hierarchy list but fall through for extra candidates
                return hr
            }
        }
    }
    // fallback
    list := tree.BuildPropertyList(properties, types)
    return tree.RecommendProperty(list)
}

/* ------------------------------------------------------------------ */
/*  Helper: convert strings → IList                                    */
/* ------------------------------------------------------------------ */

// BuildPropertyList turns input strings into an IList of *IItem used by SchemaTree.
func (tree *SchemaTree) BuildPropertyList(properties []string, types []string) IList {

	list := []*IItem{}

	// property strings
	for _, pString := range properties {
		if p, ok := tree.PropMap.GetIfExisting(pString); ok {
			list = append(list, p)
		}
	}

	// type strings ("t#<type>")
	for _, tString := range types {
		key := "t#" + tString
		if p, ok := tree.PropMap.GetIfExisting(key); ok {
			list = append(list, p)
		}
	}

	return list
}


// RecommendProperty recommends a ranked list of property candidates by given IItems
func (tree *SchemaTree) RecommendProperty(properties IList) (ranked PropertyRecommendations) {

	if len(properties) > 0 {

		properties.Sort() // descending by support

		pSet := properties.toSet()

		candidates := make(map[*IItem]uint32)

		var makeCandidates func(startNode *SchemaNode)
		makeCandidates = func(startNode *SchemaNode) { // head hunter function ;)
			for _, child := range startNode.Children {
				if child.ID.IsProp() {
					candidates[child.ID] += child.Support
				}
				makeCandidates(child)
			}
		}

		// the least frequent property from the list is farthest from the root
		rarestProperty := properties[len(properties)-1]

		var setSupport uint64
		// walk from each "leaf" instance of that property towards the root...
		for leaf := rarestProperty.traversalPointer; leaf != nil; leaf = leaf.nextSameID { // iterate all instances for that property
			if leaf.prefixContains(properties) {
				setSupport += uint64(leaf.Support) // number of occurences of this set of properties in the current branch

				// walk up
				for cur := leaf; cur.parent != nil; cur = cur.parent {
					if !(pSet[cur.ID]) {
						if cur.ID.IsProp() {
							candidates[cur.ID] += leaf.Support
						}
					}
				}
				// walk down
				makeCandidates(leaf)
			}
		}

		// now that all candidates have been collected, rank them
		setSup := float64(setSupport)
		ranked = make([]RankedPropertyCandidate, 0, len(candidates))
		for candidate, support := range candidates {
			ranked = append(ranked, RankedPropertyCandidate{candidate, float64(support) / setSup})
		}

		// sort descending by support
		sort.Slice(ranked, func(i, j int) bool { return ranked[i].Probability > ranked[j].Probability })
	} else {
		// TODO: Race condition on propMap: fatal error: concurrent map iteration and map write
		// fmt.Println(tree.Root.Support)
		setSup := float64(tree.Root.Support) // empty set occured in all transactions
		ranked = make([]RankedPropertyCandidate, tree.PropMap.Len())
		for _, prop := range tree.PropMap.noWritersList_properties() {
			ranked[int(prop.SortOrder)] = RankedPropertyCandidate{prop, float64(prop.TotalCount) / setSup}
		}
	}

	return
}

// RecommendPropertiesAndTypes recommends a ranked list of property and type candidates by given IItems
func (tree *SchemaTree) RecommendPropertiesAndTypes(properties IList) (ranked PropertyRecommendations) {

	if len(properties) > 0 {

		properties.Sort() // descending by support

		pSet := properties.toSet()

		candidates := make(map[*IItem]uint32)

		var makeCandidates func(startNode *SchemaNode)
		makeCandidates = func(startNode *SchemaNode) { // head hunter function ;)
			for _, child := range startNode.Children {
				candidates[child.ID] += child.Support
				makeCandidates(child)
			}
		}

		// the least frequent property from the list is farthest from the root
		rarestProperty := properties[len(properties)-1]

		var setSupport uint64
		// walk from each "leaf" instance of that property towards the root...
		for leaf := rarestProperty.traversalPointer; leaf != nil; leaf = leaf.nextSameID { // iterate all instances for that property
			if leaf.prefixContains(properties) {
				setSupport += uint64(leaf.Support) // number of occuences of this set of properties in the current branch

				// walk up
				for cur := leaf; cur.parent != nil; cur = cur.parent {
					if !(pSet[cur.ID]) {
						candidates[cur.ID] += leaf.Support
					}
				}
				// walk down
				makeCandidates(leaf)
			}
		}

		// now that all candidates have been collected, rank them
		setSup := float64(setSupport)
		ranked = make([]RankedPropertyCandidate, 0, len(candidates))
		for candidate, support := range candidates {
			ranked = append(ranked, RankedPropertyCandidate{candidate, float64(support) / setSup})
		}

		// sort descending by support
		sort.Slice(ranked, func(i, j int) bool { return ranked[i].Probability > ranked[j].Probability })
	} else {
		// TODO: Race condition on propMap: fatal error: concurrent map iteration and map write
		// fmt.Println(tree.Root.Support)
		setSup := float64(tree.Root.Support) // empty set occured in all transactions
		ranked = make([]RankedPropertyCandidate, tree.PropMap.Len())
		for _, prop := range tree.PropMap.noWritersList_properties() {
			ranked[int(prop.SortOrder)] = RankedPropertyCandidate{prop, float64(prop.TotalCount) / setSup}
		}
	}

	return
}
