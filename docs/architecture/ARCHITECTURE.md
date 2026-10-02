# System Architecture

## Goal
Build a source-traceable platform for historical Arabic manuscripts. The original page image remains authoritative; every derived layer must be linked back to page coordinates.

## Major components

### 1. Manuscript ingestion
- IIIF / image / PDF import
- page ordering and metadata
- image normalization without destroying the archival original
- page-region segmentation

### 2. HTR layer
- handwritten Arabic text recognition
- pluggable engines (Kraken/eScriptorium first)
- model/version metadata per recognition job
- confidence score per line/token
- manual correction workflow

### 3. Text layers
Each page can contain multiple distinct text representations:
1. diplomatic transcription
2. verified transcription
3. normalized Arabic
4. simplified modern Arabic
5. translations
6. AI explanation

These layers must never be merged into a single field.

### 4. Interactive viewer
- synchronized manuscript image + text
- click line -> highlight source polygon
- click text -> highlight manuscript region
- zoom/pan
- RTL-first interface
- page comparison mode
- optional audio playback

### 5. Knowledge / AI layer
- retrieval constrained to approved manuscript corpus
- answers cite manuscript/page/region
- uncertainty exposed to the user
- no silent alteration of verified text
- historical medical/scientific content labelled as historical context, not modern professional advice

### 6. Research/editor workspace
- approve/reject HTR output
- track corrections
- compare witnesses
- annotate drawings, instruments, people, places, terminology
- provenance log

## Initial deployment model
- Web app: TypeScript
- Android app: Kotlin + Jetpack Compose
- API: Python + FastAPI
- Database: PostgreSQL
- Object storage: S3-compatible
- Search/vector retrieval: PostgreSQL + pgvector initially
- HTR workers: Python containers
- Queue: Redis-backed worker queue initially

## Data integrity rule
Every generated explanation or normalization should be traceable to:
- manuscript id
- page id
- source region
- transcription revision
- model/version
- creation timestamp
