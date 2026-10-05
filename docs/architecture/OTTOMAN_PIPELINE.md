# Ottoman Lab foundation

The historical language scope is Arabic, Ottoman Turkish and Persian. This scope does not
remove Urdu or any other existing interface locale. Ottoman is a scholarly workflow, not a UI language.

The pipeline stores independent immutable revisions: layout → HTR → original-script
transcription → Latin transliteration → Modern Turkish → Arabic/English translations.
Each record has its own confidence (unknown by default), review state, source manuscript,
witness/page/region/coordinates, model/method, timestamp, reviewer and upstream revision.
Original images remain on Page and are returned by the pipeline endpoint.

`POST /api/v1/ottoman/revisions` accepts authenticated scientific edits.
`GET /api/v1/ottoman/manuscripts/{id}/pages/{page}` returns original and revision history.
`GET /api/v1/ottoman/stages` advertises stages/languages and provider availability.
The web reader offers an Ottoman Lab panel next to living layers. It saves manual readings,
transliterations, modernization and translations with explicit upstream selection. HTR records
are imported model outputs, always machine state; no installed HTR/translation provider is claimed.
Layout can be authored through API; the first UI focuses on text stages.

Human reading may start directly from the source image without requiring a machine reading.
Human verification of HTR creates a separate transcription. Downstream verification requires
reviewed upstream text. Draft downstream work may cite unreviewed text and keeps draft state.
Upstream and output must share manuscript/page/witness/region. Parent-head conflicts return 409;
invalid stage transitions or cross-page derivation return 422. Reviewer identities must match the
signed token; ordinary editors cannot approve their own output by changing a field.

Storage uses OTTOMAN_METADATA_PATH (default ./data/ottoman.sqlite3). Schema version 1
and tables are created idempotently, retaining existing records. Every append writes an actor,
server timestamp and upstream/parent IDs in the same SQLite transaction. Use SQLite backup API
for live backups, or stop writes and copy the database; test a restored copy before replacement.
No images are duplicated or large models loaded into the 1 GB application server.

The tests use explicitly synthetic strings, not invented historical examples. A reviewed teaching
corpus, academy/dictionary, automatic model adapter and native Android lab UI remain later slices.
