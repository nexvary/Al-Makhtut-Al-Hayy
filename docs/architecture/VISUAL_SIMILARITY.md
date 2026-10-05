# Visual discovery provider boundary

VisualQuery identifies a documented source region and a fragment/illustration/handwriting/layout
task. VisualSimilarityProvider returns candidate source provenance, similarity score and model
identity. Similarity is not evidence of authorship, copying or a related witness. A historian must
review those proposed relationships separately and record evidence in the knowledge graph.

The default DisabledVisualProvider raises ProviderUnavailable. No fake similarity result, model
or index is exposed to users, and no disabled search button is added to the reader. An external
GPU/API worker can implement the protocol later. Upload bytes must go through a bounded
StorageProvider; remote image fetching must retain public-source validation, rights and cache
limits. API inference routes and embeddings ingestion are deferred until a real provider exists.
This contract is tested for explicit unavailability, not claimed as an operational visual engine.
