# Open-Source Technology Map

This document records candidate upstream components for **Al-Makhtut-Al-Hayy**.

## Core stack

| Component | Planned role | Integration decision |
|---|---|---|
| Kraken | Arabic/non-Latin HTR, segmentation, recognition | Primary HTR engine adapter |
| eScriptorium | HTR training, transcription and human correction | Preferred research/editor workbench |
| IIIF Presentation/Image APIs | Manuscript manifests, canvases, deep-zoom images | Primary interoperability standard |
| OpenSeadragon | High-resolution manuscript viewer | Primary low-level viewer |
| Mirador | IIIF research/comparison viewer | Interoperability / advanced comparison target |
| Annotorious | Image annotation interaction model | Evaluate for editor annotations; keep internal format independent |
| FastAPI | Product/backend API | Primary API service |
| PostgreSQL + pgvector | Metadata, revisions, citations, retrieval | Initial persistence/search layer |

## Arabic manuscript datasets / reference projects

### OpenITI / MAKHZAN
Use:
- evaluation/training research,
- Arabic-script corpus experiments,
- interoperability/reference data.

Rule:
Check the licence of the exact release/artifact before redistribution.

### AraMS-28k
Use:
- Arabic historical manuscript layout/HTR experiments,
- difficult page layout and marginalia evaluation.

Constraint:
Treat as research-only by default until the exact dataset licence and intended distribution model are reviewed.

### Muharaf
Use:
- benchmark/evaluation and Kraken model experiments.

Constraint:
Do not bundle weights/data into a commercial distribution until their licences are reviewed.

### HTR-United
Use:
- discover interoperable ground-truth datasets,
- ALTO/PAGE-style workflow evaluation.

### ArchaText HTR/OCR Workbench
Use:
- architectural reference,
- compare practical FastAPI + Kraken orchestration patterns.

Rule:
Reuse only code that is licence-compatible and preserve required notices.

## Integration rules

1. **No vendor lock-in**
   All HTR engines implement an internal adapter contract.

2. **No dataset contamination**
   Training/evaluation datasets must have a recorded licence and provenance.

3. **No hidden AI rewrite**
   Raw HTR, verified transcription, normalized Arabic and AI explanation are separate layers.

4. **Geometry is first-class**
   Every text segment should retain a polygon/baseline/region that points back to the source image.

5. **IIIF first**
   If a library exposes IIIF, prefer its manifest and image service instead of downloading/rehosting images.

6. **Rights before ingestion**
   Store source institution, source URL and use/licence terms before running HTR or publishing derived assets.

## First live-source candidate

**BnF / Gallica — Al-Zahrawi, Al-Tasrif, article 30 / surgery**
- Biblissima record: https://iiif.biblissima.fr/collections/manifest/c02ca84ba85c8151f51ecff51d001bd44e37434b
- Gallica IIIF manifest: https://gallica.bnf.fr/iiif/ark:/12148/btv1b84061750/manifest.json
- Description indicates Arabic/Maghribi script and drawings of instruments.

Important:
Do not copy Gallica images into this repository. Access them through the source/IIIF service and respect Gallica's usage conditions.

## Public-domain fallback for engineering tests

Wellcome Collection exposes Arabic manuscript material marked Public Domain. These can be useful for test fixtures when unrestricted image reuse is required. Source credit and metadata should still be retained.

## Licence gate

Before any dataset/model/source is promoted from "evaluation" to "production", record:
- upstream name/version,
- source URL,
- software licence,
- data/image licence,
- model licence,
- attribution requirements,
- commercial-use restrictions,
- redistribution restrictions,
- date reviewed.
