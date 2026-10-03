BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS manuscripts (
    id text PRIMARY KEY,
    title text NOT NULL,
    author text,
    date_label text,
    source_institution text,
    source_url text,
    rights text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pages (
    id text PRIMARY KEY,
    manuscript_id text NOT NULL REFERENCES manuscripts(id) ON DELETE CASCADE,
    sequence integer NOT NULL,
    folio_label text,
    image_uri text NOT NULL,
    canvas_uri text,
    image_width integer,
    image_height integer,
    UNIQUE (manuscript_id, sequence)
);

CREATE TABLE IF NOT EXISTS regions (
    id text PRIMARY KEY,
    page_id text NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    region_type text NOT NULL,
    reading_order integer,
    polygon jsonb NOT NULL DEFAULT '[]'::jsonb
);

CREATE TABLE IF NOT EXISTS text_layers (
    id bigserial PRIMARY KEY,
    region_id text NOT NULL REFERENCES regions(id) ON DELETE CASCADE,
    kind text NOT NULL,
    text text NOT NULL,
    status text NOT NULL,
    confidence double precision,
    model text,
    revision text,
    embedding vector(768),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS text_layers_region_idx ON text_layers(region_id);
CREATE INDEX IF NOT EXISTS text_layers_search_idx
    ON text_layers USING gin (to_tsvector('simple', text));

CREATE TABLE IF NOT EXISTS provenance_events (
    id bigserial PRIMARY KEY,
    manuscript_id text NOT NULL,
    page_id text,
    region_id text,
    event_type text NOT NULL,
    agent_kind text NOT NULL,
    agent_id text NOT NULL,
    model_id text,
    source_uri text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations(version)
VALUES ('001_initial')
ON CONFLICT (version) DO NOTHING;

COMMIT;
