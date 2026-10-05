# AI Grounding Contract

The AI layer is downstream of retrieval and may not silently create a source.

Rules:
1. Search operates on region/page documents with stable citation targets.
2. Verified transcription receives a ranking boost, but raw HTR can remain discoverable when explicitly requested.
3. Generated factual claims must cite one or more returned evidence IDs.
4. Unknown evidence IDs are rejected.
5. If no relevant evidence is retrieved, the response is marked `insufficient_evidence`.
6. Generated explanations are never stored as verified transcription.
7. Any future LLM provider is an adapter behind this contract.
8. The user must be able to jump from evidence to manuscript/page/region.

## Scoped Manuscript AI Lab

`POST /api/v1/ai-lab/ask` accepts a source anchor, task and question. The current
EvidenceOnlyAI adapter searches persisted living representations at exactly that page/region,
selects current revisions and returns excerpts with full provenance and review state. It does
not turn similarity or a user's question into a claimed reading. Translation/explanation tasks
require previously stored layers of that kind; absence returns insufficient_evidence. Unknown
confidence remains null. The UI exposes task/source/results alongside the original image.
An AIService protocol separates external/GPU providers from the application process; no large
model or synthetic answer is run on the VPS. Future generated answers need independent
claim/evidence validation; citing a source alone does not prove factual entailment.

## Ask the Heritage foundation

POST /api/v1/heritage/ask retrieves current reviewed text representations from the durable
living-layer store across manuscripts. Work, manuscript and language filters are available.
The response carries full page/region/witness provenance, revision, confidence and an explicit
retrieval score. Retrieval score is not scholarly confidence. No unsupported generated synthesis
is returned; no matching evidence gives insufficient_evidence. Previous versions replaced by a
new current revision are not silently used as the latest reading. Original manuscript text stays
unchanged. This initial bounded lexical adapter examines at most 2,000 recent current verified
representations; complete large-corpus retrieval requires an indexed/vector adapter. EvidenceCorpus
provides that boundary. Ottoman pipeline records must be deliberately published as reviewed living
representations before entering this corpus; machine records are never auto-promoted.
