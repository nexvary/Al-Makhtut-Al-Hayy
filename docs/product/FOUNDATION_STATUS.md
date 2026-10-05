# Verified implementation scope

Work branch: `dev/foundation`. No merge into `main` is authorized yet.

## Android release gate

Commit `1e1aa8dc8e388ec68b0e1c7f48f5139411992113`: Android CI and Android 15 UI Smoke
are green. Android CI runs unit tests, instrumentation compilation, lint and assembleDebug.
Smoke runs fourteen tests in each Arabic/English locale at 360×640 dp on API 35, covering
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
The Android remote reader now displays scoped layer history and evidence-only lab results (native CI validation required for each release). Ottoman stages, dictionary and Academy exercises are now integrated with native Android. Heritage graph/time/museum integration passed native API 35 smoke in Arabic and English. The web reader displays layer history in learner/researcher views and allows authenticated
creation of drafts and reviewed text. Tokens are entered explicitly and are not persisted.
Human verification is restricted to Reviewer/Administrator and tied to the authenticated actor.
Concurrent writes to one layer scope use parent-revision checks; stale writes return 409.
Source, scholarly metadata and layer audit entries are committed atomically with changes.

Current local validation: 66 API tests, 6 HTR tests, Ruff and web TypeScript/Vite build.
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
Ask the Heritage retrieves reviewed source excerpts. A bounded thumbnail fingerprint index and real image query now support visual candidate discovery in the API/web. No automatic Ottoman translation, complete academy corpus, generated 3D
models, large-scale semantic RAG or handwriting identification is claimed. See the architecture
documents for exact limits. The web visual-search source action opens the exact page/region and its original image; a two-page browser fixture guards against accidentally opening the first page or retaining another manuscript image.
Legacy editorial, glossary, visual knowledge and lexical search now persist in SQLite with append-only histories/audit. Their older schemas remain compatibility contracts; they are not automatically promoted into verified living-layer or museum records. Lexical retrieval scans at most 2,000 recent documents; semantic-only vector candidates can resolve stored source documents. Persistent accounts now support login, roles, disable/password reset, immediate managed-session revocation and audit; first Administrator bootstrap has no default password. Legacy manually signed tokens remain compatible and are revoked by secret rotation, not account logout. Real deployment identity and corpus onboarding remain operational work.

## Light operations profile

Single-worker, non-root Docker profile with durable metadata volumes, bounded requests and
streaming storage is provided for the 1 GB VPS. SQLite backup/restore fixture tests run locally;
Docker startup/restart is checked by Backend CI. The real VPS has not been deployed or load tested.
