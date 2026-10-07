# System Architecture

## Goal
Build a source-traceable platform for historical Arabic manuscripts. The original page image remains authoritative; every derived layer must be linked back to page coordinates and provenance.

## Architecture principle: integrate, do not reinvent
The project should not build a handwriting-recognition stack from zero. It integrates mature open-source/document standards behind stable internal interfaces so components can be replaced without changing the product data model.

## Major components

### 1. Manuscript ingestion
Primary standards and sources:
- IIIF Presentation API for manifests/canvases.
- IIIF Image API for zoomable source images where available.
- local image/PDF import as a fallback.
- ALTO XML / PAGE XML import for OCR/HTR geometry.

Responsibilities:
- page ordering and metadata.
- image normalization without altering the archival original.
- page-region segmentation.
- rights/licence/provenance capture before processing.

### 2. HTR layer
Primary engine:
- Kraken for Arabic/non-Latin HTR, segmentation, recognition and geometry.
- eScriptorium as the preferred training/transcription/review workbench.

Design:
- HTR engines are adapters, not hard-coded dependencies.
- persist model name/version/checksum per recognition job.
- persist confidence per region/line/token where the engine provides it.
- retain raw engine output for reproducibility.
- human review creates a new revision; it never overwrites the raw HTR layer.

### 3. Text layers
Each page can contain multiple distinct text representations:
1. raw HTR output
2. diplomatic transcription
3. verified transcription
4. normalized Arabic
5. simplified modern Arabic
6. translations
7. AI explanation

These layers must never be silently merged.

### 4. Interactive viewer
Web stack:
- OpenSeadragon for deep zoom and coordinate transforms.
- IIIF manifests as the preferred page transport.
- Annotorious-style annotation model or a compatible internal overlay layer for regions.
- Mirador interoperability is a target for research/comparison workflows.

UX:
- synchronized manuscript image + text.
- click line -> highlight source polygon.
- click text -> highlight manuscript region.
- zoom/pan.
- RTL-first interface.
- page comparison mode.
- optional audio playback.
- clear badges for Machine / Draft / Human Verified.

### 5. Knowledge / AI layer
- retrieval constrained to approved manuscript corpus.
- answers cite manuscript/page/region.
- retrieved evidence is shown separately from generated explanation.
- uncertainty exposed to the user.
- no silent alteration of verified text.
- historical medical/scientific content is labelled as historical context, not modern professional advice.

### 6. Research/editor workspace
- approve/reject/correct HTR output.
- track corrections as revisions.
- compare manuscript witnesses.
- annotate drawings, instruments, people, places and terminology.
- provenance and audit log.
- export/import interoperable formats where practical.

## Open-source/data inputs
The project may evaluate:
- Kraken
- eScriptorium
- Mirador
- OpenSeadragon
- Annotorious
- OpenITI/MAKHZAN
- AraMS-28k
- Muharaf
- HTR-United Arabic datasets
- ArchaText HTR/OCR workbench

Dataset/software licences must be reviewed independently. A model or dataset suitable for research is not automatically suitable for commercial redistribution.

## Initial deployment model
- Web app: TypeScript + Vite.
- Android app: Kotlin + Jetpack Compose.
- API: Python + FastAPI.
- Database: PostgreSQL.
- Object storage: S3-compatible.
- Search/vector retrieval: PostgreSQL + pgvector initially.
- HTR workers: Python containers.
- Queue: Redis-backed worker queue initially.

## Internal contracts
The system should define internal contracts for:
- IIIF/source ingestion.
- HTR job request/result.
- region geometry.
- text layer/revision.
- provenance.
- citation target.
- annotation.
- viewer selection events.

This isolates the product from any one OCR/HTR provider.

## Data integrity rule
Every generated explanation, normalization or transcription revision should be traceable to:
- manuscript id.
- page id.
- source region.
- source URI / IIIF canvas when applicable.
- transcription revision.
- HTR/model version.
- processor identity (machine/editor).
- creation timestamp.

## Compatibility durability

Older editorial, glossary, visual-knowledge and lexical-index contracts now use
`LEGACY_METADATA_PATH` on the metadata volume. Current records have immutable historical
snapshots and hash-linked audit entries; HTTP glossary/visual writes record the authenticated
actor. Editorial revisions retain atomic head/parent checks and immutable IDs. HTR output
cannot become verified under the same machine-reading kind. Earlier in-memory process state
cannot be recovered after that process exited; no invented migration data is created.

Compatibility schemas do not acquire verified provenance automatically. New scholarly
editing uses living layers and museum contracts; legacy objects remain legacy objects.
Lexical search scans at most 2,000 current documents and retains bounded top results.
Vector-only candidates can resolve an actual stored source document; unknown IDs are skipped.
The default vector adapter still has no external embedding service. Restart, revision-parent,
legacy data and vector-only source-resolution tests cover these contracts.
