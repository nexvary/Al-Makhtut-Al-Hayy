# المخطوط الحي — Living Manuscript

**Al-Makhtut-Al-Hayy** is an independent open-source platform for turning historical Arabic manuscripts into interactive, readable, searchable, and explainable digital experiences.

## Vision
Preserve the original manuscript image while adding an interactive knowledge layer that can:
- recognize handwritten Arabic (HTR/OCR),
- align detected text with the original page,
- provide verified transcription and normalized Arabic,
- explain difficult vocabulary and historical context,
- read passages aloud,
- answer questions with page/line citations,
- compare manuscript witnesses,
- connect illustrations and historical instruments to interactive media.

## Foundation stack
- **IIIF** for manuscript manifests and image interoperability.
- **OpenSeadragon** for deep-zoom manuscript reading.
- **Kraken** behind a pluggable HTR adapter.
- **eScriptorium** as the preferred training/correction workbench.
- **FastAPI** for product APIs.
- **PostgreSQL + pgvector** planned for provenance, metadata and retrieval.
- **Kotlin + Jetpack Compose** planned for Android.

## Current prototype
The `dev/foundation` branch contains the first web viewer:
- IIIF Presentation v2/v3 loading,
- deep zoom,
- page navigation,
- RTL interface,
- synchronized region/text selection,
- separate machine / verified / normalized text layers.

Its default source points to an external Gallica IIIF manifest for a manuscript of Al-Zahrawi's surgical section. Images are not copied into this repository.

> The current prototype regions/text are demonstrative only and are **not** claimed transcriptions of the displayed manuscript. Real regions will come from the HTR/review pipeline.

## Planned products
- Web reader
- Android app
- AI/HTR backend
- Manuscript processing pipeline
- Research/editor verification tools
- Optional 3D/audio/animation modules

## Core principle
The original manuscript remains the primary source. AI-generated text must be clearly separated from verified transcription and must preserve traceability to the source page/region.

## Repository structure
```
apps/
  web/
  android/
services/
  api/
  htr/
  ai/
packages/
  manuscript-schema/
  viewer-core/
docs/
  architecture/
  research/
  product/
```

## Research
See:
- `docs/research/OPEN_SOURCE_TECH_MAP.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/product/ROADMAP.md`

## Status
Foundation + first IIIF viewer prototype.
