# Visual discovery

A real light provider now fingerprints curated PNG/JPEG thumbnails with a 64-bit difference
hash and searches durable SQLite descriptors. `/api/v1/visual-search/query` accepts a bounded
image fragment or illustration and returns source-linked candidates. The web reader can upload
a small image and open candidate manuscripts. Similarity is not attribution or scholarly confidence.
Handwriting and semantic/layout identification are rejected by this provider. They remain worker
provider scope; the existing protocol can accept a different implementation.

Only Reviewers/Administrators can index a thumbnail. They attest that it is a derivative of the
recorded original image and that the recorded manuscript license permits indexing. The API checks
source existence, original URI and license identity; it cannot prove byte identity with an external
original without fetching it. Original images are never downloaded by this feature. Raw query and
index thumbnails are discarded after processing; descriptors, digest, curator, rights and source
are retained with an audit entry. Publishing identical source/kind/image bytes is idempotent.

Inputs are limited to 1 MiB and one megapixel. Only single-frame PNG/JPEG are decoded, one at a
time; blank thumbnails are rejected. Up to 10,000 index entries fit the initial profile; retrieval
retains only 30 top candidates rather than materializing all provenance records. SQLite backup
automatically includes `visual-index.sqlite3`. The Docker path is on the metadata volume.

Tests cover persistence, limits, unsupported tasks, roles, rights and live API queries. Browser CI
uses a clearly synthetic image fixture to exercise upload, candidate source and score labeling.
Pillow decoding follows its documented format allowlist and pixel-bound guidance:
https://pillow.readthedocs.io/en/stable/handbook/security.html
