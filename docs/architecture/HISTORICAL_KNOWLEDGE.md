# Historical graph, Time Machine and map foundation

HistoricalEntity and HistoricalRelation are source-backed, independently reviewed records.
Entities cover people/authors/scholars, books/works/manuscripts, cities/countries/places,
events, instruments, medicines/plants, concepts and institutions. Relations refer to known
entity IDs, preserve their predicate and source, and reject dangling links. Unknown dates or
coordinates remain null. Metadata writes append immutable revisions with parent-head checks
and atomic actor/time audit. Verification requires the authenticated reviewer.

GET /api/v1/heritage/entities?q=… searches names/aliases. GET /entities/{id} returns the
entity and its documented neighborhood. POST /entities and /relations require editor roles.
No external historical facts or fixed sample cards are seeded into real data. Web results query
the repository and can expand relations; drafts remain visibly marked as drafts.

Time Machine accepts an inclusive start/end year interval. Only entities with documented
intervals that overlap are returned; undated entities are not invented into a century. BCE uses
signed proleptic-Gregorian years; source calendar conversions must be explicitly authored with
provenance. Circa dates remain marked approximate. Life spans, creation intervals and events
must be modeled deliberately, not confused with a manuscript's present custody.

GET /api/v1/heritage/map returns GeoJSON point features. Optional start/end filters use the
same interval semantics. GeoJSON coordinates are longitude, latitude; location bounds and
finite numbers are validated. The web lists sourced coordinates and links to an external map.
Historical borders, movement routes and embedded interactive map tiles remain future work.
Creation/custody/life/travel relations can be authored as separate predicates with intervals;
a current library location must not be claimed as a historical creation site.

HERITAGE_METADATA_PATH defaults to ./data/heritage.sqlite3. Tables/indexes are created
idempotently; records survive restart. Back up through SQLite backup API or stop writes before
copying. The schema/provider boundary does not require Neo4j or a large graph service on the
1 GB VPS; future graph infrastructure can replace this adapter. User scientific text is rendered
with textContent. The service never fetches submitted location URLs.
