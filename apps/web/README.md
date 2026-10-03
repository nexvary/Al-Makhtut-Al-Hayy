# Web Prototype

First interactive viewer for **Al-Makhtut-Al-Hayy**.

## What works
- Loads IIIF Presentation v2/v3 manifests.
- Opens deep-zoom image services with OpenSeadragon.
- RTL Arabic interface.
- Previous/next page navigation.
- Demonstrates synchronized image-region ↔ transcription selection.
- Keeps HTR / human-verified / normalized Arabic as separate UI layers.
- Defaults to an external Gallica IIIF manifest for Al-Zahrawi's surgical section.

The current region polygons/text are intentionally demo data. They are not claimed transcriptions of the displayed manuscript.

## Run
```bash
cd apps/web
npm install
npm run dev
```

## Build
```bash
npm run build
```

## Source policy
The default manuscript image is loaded remotely from the institution's IIIF service. It is not stored or redistributed by this repository. Review the source institution's usage terms before publication or commercial deployment.

## Next integration
Replace `demoRegions` with API data produced by:
1. IIIF ingestion,
2. Kraken segmentation/HTR,
3. editor verification,
4. normalization/AI services.
