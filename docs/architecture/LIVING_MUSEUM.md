# Living Museum, historical objects and 3D contracts

MuseumObject connects an original illustration region to a documented description or an
explicit interpretive reconstruction. Its source region must match the preserved source
anchor and documentary evidence is required. Reconstruction must disclose assumptions.
Assets carry their own provenance, review state, attribution, license and evidence class.
3D geometry is always labeled interpretive reconstruction; it is not passed off as original
historical evidence. No automatic object detection, model generation or large GPU inference
is performed by this implementation.

Exhibition groups known object IDs with a theme, context and source. Unknown objects are
rejected. Both objects and exhibitions append immutable revisions with parent-head conflicts
and actor/time audit. POST /api/v1/museum/objects and /exhibitions require a curator
(Reviewer/Administrator). Verified records require matching authenticated reviewer identity.
GET /exhibitions and /exhibitions/{id} supply the web museum. Original source IDs and regions
remain visible; assets are external links with evidence/interpretation labels and attribution.

MUSEUM_METADATA_PATH defaults to ./data/museum.sqlite3; use consistent SQLite backups.
The existing /visual prototype remains compatible and is not silently migrated into the new
museum. Full interactive galleries, audio narration, model viewing and historical corpus are
future slices; this is a durable, source-aware museum foundation with tested browse behavior.
