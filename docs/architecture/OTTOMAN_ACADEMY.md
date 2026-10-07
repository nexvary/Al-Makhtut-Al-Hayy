# Ottoman Academy and smart dictionary foundation

The dictionary is an independently reviewed lexical record: original spelling, Latin
transliteration, Modern Turkish, Arabic/English meanings, historical/grammatical notes,
related forms, source examples, confidence and provenance. Unknown fields stay null.
Etymology is accepted only in a verified entry with explicit documentary evidence and an
authenticated reviewer. This is an editorial safeguard, not automatic linguistic verification.
The source anchors/evidence must resolve to stored pages/regions. No invented etymology or
unsourced vocabulary is shipped. Entries are append-only with parent-head conflicts and audit.

GET /api/v1/ottoman/dictionary?q=… searches current entry revisions. POST requires an editor;
verified entries require a reviewer. Search is NFC/whitespace/case normalization, not a claim
that distinct Ottoman spellings are equivalent. Manuscript examples remain source anchored.

Learn Ottoman From The Manuscript uses immutable verified Ottoman stage revisions.
A reviewer creates a ReadingExercise referencing original-script transcription and optionally
one continuous transliteration → Modern Turkish → Arabic chain. All referenced outputs must
be verified, on the specified source page, and the manuscript's recorded license must match
the exercise source_license. The reviewer records the permitted educational use in rights_note;
license matching alone is not a legal rights determination.

The learner sees the original image in the reader, attempts the reading, and can reveal each
stored stage. Exercise listing withholds answer text. Feedback performs only NFC/whitespace
exact comparison; a mismatch is not a declaration that every alternative reading is wrong.
Attempts are not retained; tokens are unnecessary for public learning. Authors create exercises
through the API; the web panel supplies dictionary lookup and progressive practice.

ACADEMY_METADATA_PATH defaults to ./data/academy.sqlite3. Dictionaries and exercises survive
restart. Schema creation is idempotent. Scientific edits are authenticated and audited in the
same transaction. Back up using SQLite backup API or stop writes before copying. The reviewed
alphabet/letter-form/course corpus, handwriting feedback and teaching author UI are future work;
no full academy curriculum is claimed by this foundation slice.
