CREATE TABLE IF NOT EXISTS indexed_files (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL,
    collection  TEXT NOT NULL,
    file_hash   TEXT NOT NULL,
    indexed_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (filename, collection)
);
