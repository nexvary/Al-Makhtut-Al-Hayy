# Living manuscript model and provenance

`Manuscript` references optional bibliographic Work/Witness IDs. Pages retain their original
image and IIIF canvas; regions retain coordinates. `LivingLayer` is a distinct representation
anchored to manuscript, witness, page and optional region/coordinates. Its schema is exported
in `packages/manuscript-schema/living-layer.schema.json` and tested against runtime Pydantic.

Machine reading, draft, verified, critical, modernized, explanation, translation, audio, entities,
objects, illustrations, references, annotations and provenance are independent layer kinds.
Original images are read from the source Page and rejected by the layer-write endpoint.
Machine output must name its model; it cannot be promoted in place. Verification creates a
new reviewed representation, names the reviewer and preserves the earlier machine/draft.
Unknown confidence stays null; no confidence is invented. Alternative readings belong in
separate scholarly variant records, not an invented replacement of uncertain source text.

`POST /api/v1/living/layers` appends a revision. `parent_revision_id` must equal the latest ID
for the scope (manuscript/page/witness/region/kind/language). The SQLite transaction uses
BEGIN IMMEDIATE and appends an actor/time audit record. Conflicts return HTTP 409.
`GET /api/v1/living/manuscripts/{id}/pages/{page}/layers` includes the unchanged original
image and complete revision history. `GET /api/v1/living/audit` requires reviewer privileges.

Source anchors and evidence citations are checked against stored manuscripts/pages/regions.
Coordinates are checked against known original image dimensions; witness associations must
match the manuscript. Verified writes require a Reviewer/Administrator whose subject equals
the recorded reviewer. Legacy editorial verification also rejects ordinary transcribers.

## Persistence and deployment boundaries

Environment paths: MANUSCRIPT_METADATA_PATH, SCHOLARSHIP_METADATA_PATH and
LIVING_METADATA_PATH (defaults under ./data). Existing SQLite files migrate idempotently
by creating missing tables, preserving records. Back up all databases consistently using the
SQLite backup API while the server is live, or stop writes before copying. Restore into a
separate directory and run read/schema tests before replacing active data.

The first deployment uses one application worker; locks for source metadata remain process
local. The layer repository additionally uses SQLite transaction serialization. PostgreSQL
migration and multi-worker metadata consistency require further work. These SQLite repositories
do not silently turn legacy in-memory components into durable services. Do not deploy a 1 GB
VPS using the existing full PostgreSQL/Redis stack without an explicit resource profile.

No server filesystem or arbitrary layer asset URL is fetched by the new layer API. The web
panel renders submitted text via textContent. CORS is restricted to explicit origins, configurable
with CORS_ORIGINS; configure the real website origin before deployment. Bearer tokens are never
logged or saved by the panel. Metadata audit contains original/new values and may contain
sensitive user research: backup and access rules must cover it.
