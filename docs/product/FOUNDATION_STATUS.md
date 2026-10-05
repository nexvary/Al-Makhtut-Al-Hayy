# Verified implementation scope

Work branch: `dev/foundation`. No merge into `main` is authorized yet.

## Android release gate

Commit `483746593b1799ed039cf159c58449adac5a97f2`: Android CI and Android 15 UI Smoke
are green. Android CI runs unit tests, instrumentation compilation, lint and assembleDebug.
Smoke runs nine tests in each Arabic/English locale at 360×640 dp on API 35, covering
Back, RTL, compact controls, local PDF/images, IIIF parsing, remote controls and About intents.
PNG evidence is retained separately from the APK. These tests do not constitute coverage
of every provider/network/device combination. Gallica manifest and native image GET were
checked directly; HEAD is not a reliable availability check for that provider.

## B/C: source model and independent living layers

Persistent SQLite repositories now retain manuscripts, works, witnesses and layer revisions
across restart. Original page image pointers cannot be overwritten or removed by metadata
updates. A new witness is required for changed source images. Editorial layers are separate
from originals and append-only. Fifteen layer kinds are represented, with independent machine,
draft and verified states, source anchors, confidence, model, human reviewer and evidence.
The web reader displays layer history in learner/researcher views and allows authenticated
creation of drafts and reviewed text. Tokens are entered explicitly and are not persisted.
Human verification is restricted to Reviewer/Administrator and tied to the authenticated actor.
Concurrent writes to one layer scope use parent-revision checks; stale writes return 409.
Source, scholarly metadata and layer audit entries are committed atomically with changes.

Current local validation: 58 API tests, 6 HTR tests, Ruff and web TypeScript/Vite build.
Web CI runs real browser tests against the API at a 390 px viewport, covering layer edits,
permission failures, escaped text, persistence, Ottoman stage separation, dictionary/exercises,
graph/time/map, museum labels and corpus evidence. Browser PNG evidence is retained.
Backend CI also builds and boots/restarts the non-root read-only Docker container. The local
browser download failed; browser success is from CI, not a claimed local execution.

## Remaining release scope

Existing HTR, grounded retrieval, TEI/PAGE/ALTO, visual knowledge and witness contracts are
foundation components, not completed production labs. Scoped evidence retrieval and literal witness comparison are implemented. Ottoman Lab now stores
separate source-linked stages, with web editorial UI; Academy supplies reviewed-source exercises
and dictionary lookup. See OTTOMAN_PIPELINE.md and OTTOMAN_ACADEMY.md for verified scope.
Historical entities/relations, time filtering and GeoJSON now use durable source-backed records;
web queries browse these records. The museum distinguishes evidence from reconstruction and
Ask the Heritage retrieves reviewed source excerpts. The visual similarity provider remains
explicitly disabled. No automatic Ottoman translation, complete academy corpus, generated 3D
models, large-scale RAG or operational visual similarity engine is claimed. See the architecture
documents for exact limits and remaining native Android integration.
Legacy editorial, glossary, visual knowledge and search stores still use in-memory adapters;
these are not durable production storage. API authentication currently uses signed bearer tokens;
account lifecycle and deployment identity integration remain to be implemented.

## Light operations profile

Single-worker, non-root Docker profile with durable metadata volumes, bounded requests and
streaming storage is provided for the 1 GB VPS. SQLite backup/restore fixture tests run locally;
Docker startup/restart is checked by Backend CI. The real VPS has not been deployed or load tested.
