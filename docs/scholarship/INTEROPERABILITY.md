# Scholarship and Interoperability

## Works and witnesses
A conceptual work is separate from each physical/digital witness. A witness may be a manuscript, printed edition, scholarly edition or translation.

## Variants
Variant readings explicitly map witness IDs to text at a named locus. The platform does not select a preferred reading automatically.

## Alignment
Witness alignment is stored as region/segment pairs plus a method label. Manual and algorithmic alignments remain distinguishable.

## TEI
The initial TEI export is intentionally conservative: page breaks, line anchors and human-verified text. It is a transport baseline, not a claim of full TEI critical-edition compliance.

## IIIF
Verified transcriptions can be exported as IIIF Presentation 3 Web Annotations using `motivation: supplementing`, matching the IIIF model for OCR/transcriptions derived from a Canvas.

## ALTO/PAGE
HTR lines have serializers plus parse→serialize round-trip tests.

## Scholarly citations
Stable application citations target manuscript → page → optional region. Institution canvas URIs remain alongside the application identifier.

## Research bundle
JSON research bundles include the manuscript data model and optional witness metadata. Media files are not silently redistributed.
