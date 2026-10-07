# Editorial Workflow

1. Raw HTR output is immutable evidence.
2. A transcriber creates a diplomatic transcription revision.
3. Reviewers correct geometry/text through new revisions.
4. A reviewer/admin may mark a revision verified.
5. Normalized/simplified Arabic is stored in separate layers.
6. Every change generates an audit event.
7. Stale-parent edits are rejected instead of silently overwriting concurrent work.
8. Confidence triage prioritizes low-confidence lines but never equates machine confidence with historical truth.

Roles:
- Viewer: read only.
- Transcriber: create draft transcriptions.
- Reviewer: verify/correct.
- Admin: manage workflows and permissions.
