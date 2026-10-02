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

## Planned products
- Web reader
- Android app
- AI/HTR backend
- Manuscript processing pipeline
- Research/editor verification tools
- Optional 3D/audio/animation modules

## Core principle
The original manuscript remains the primary source. AI-generated text must be clearly separated from verified transcription and must preserve traceability to the source page/region.

## Initial architecture
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

## Status
Foundation phase.
