CREATE TABLE IF NOT EXISTS document_profiles (
    id              SERIAL PRIMARY KEY,
    filename        TEXT NOT NULL,
    collection      TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    file_size_bytes BIGINT,
    num_pages       INTEGER,
    num_words       INTEGER,
    num_tokens      INTEGER,
    file_hash       TEXT NOT NULL,
    profiled_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE (filename, collection)
);
