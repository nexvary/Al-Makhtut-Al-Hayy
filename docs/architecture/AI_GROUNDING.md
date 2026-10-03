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
