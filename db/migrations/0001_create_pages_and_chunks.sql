CREATE TABLE IF NOT EXISTS pages (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id        uuid NOT NULL,
    category      text NOT NULL,
    url           text NOT NULL UNIQUE,
    status        text NOT NULL CHECK (status IN ('discovered', 'scraped', 'failed', 'embedded')),
    title         text,
    content       text,
    content_hash  text,
    discovered_at timestamptz NOT NULL DEFAULT now(),
    scraped_at    timestamptz
);

CREATE INDEX IF NOT EXISTS pages_run_id_idx ON pages (run_id);
CREATE INDEX IF NOT EXISTS pages_status_idx ON pages (status);

CREATE TABLE IF NOT EXISTS chunks (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id    uuid NOT NULL REFERENCES pages (id) ON DELETE CASCADE,
    heading    text,
    content    text NOT NULL,
    embedding  vector(384) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chunks_page_id_idx ON chunks (page_id);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
