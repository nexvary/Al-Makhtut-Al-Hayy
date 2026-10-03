# Historical Visual Knowledge

The visual layer turns manuscript drawings into discoverable historical objects without presenting reconstructions as primary evidence.

## Object
A historical object can point to one or more manuscript regions and citations. Media such as a clean illustration, audio, animation or GLB/GLTF model is secondary material and carries its own licence/attribution.

## Instrument gallery
`GET /api/v1/visual/objects?manuscript_id=...` is the initial gallery feed.

## Timeline
Events use explicit years, optional end years, and a `circa` flag. They may cite manuscript regions.

## Places
Objects can reference places with coordinates only when known; no coordinate is invented from a vague historical name.

## 3D
3D models are external media assets. Their licence is independent of the manuscript image.

## Historical medical context
Medical, surgical and pharmacy objects automatically receive a historical-context warning. Historical descriptions must not be presented as modern medical instructions.

## Related passages
The graph links explicit region IDs and a named relationship. It does not infer equivalence silently.

## Curated exhibits
An exhibit is an ordered educational collection of objects and source-aware story cards.
