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

Local validation: 33 API tests and web TypeScript/Vite build. Browser test runs in Web CI;
local browser installation failed, so no local browser success is claimed.

## Remaining release scope

Existing HTR, grounded retrieval, TEI/PAGE/ALTO, visual knowledge and witness contracts are
foundation components, not completed production labs. Scoped evidence retrieval and literal witness comparison are implemented. Ottoman Lab now stores
separate source-linked stages, with web editorial UI; Academy supplies reviewed-source exercises
and dictionary lookup. See OTTOMAN_PIPELINE.md and OTTOMAN_ACADEMY.md for verified scope.
No automatic Ottoman translation, complete academy corpus, historical graph, 3D model, external
AI provider or visual similarity service is claimed as operational. Phases H–L remain outstanding.
Legacy editorial, glossary, visual knowledge and search stores still use in-memory adapters;
these are not durable production storage. API authentication currently uses signed bearer tokens;
account lifecycle and deployment identity integration remain to be implemented.
