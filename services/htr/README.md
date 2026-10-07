# HTR Service

This package defines the product-facing contract for handwriting recognition.

## Design
Kraken is the first target engine, but manuscript data must not become Kraken-specific. The rest of the platform consumes a stable `HtrResult` containing:
- recognized text,
- line geometry,
- confidence,
- engine/model identity,
- raw artifact reference,
- source page identity.

## Planned worker flow
1. Receive an allowed source image or IIIF page reference.
2. Resolve the image.
3. Run segmentation.
4. Run Kraken recognition with a pinned model.
5. Preserve raw engine/PAGE/ALTO output.
6. Convert lines to the internal HTR contract.
7. Store provenance.
8. Create a separate editable transcription revision.

## eScriptorium
Use eScriptorium for model training and human correction. Import/export its results into the same internal region/text-layer model.

## Security
Production workers must not fetch arbitrary private-network URLs. Remote fetching requires an allowlist/proxy policy.
