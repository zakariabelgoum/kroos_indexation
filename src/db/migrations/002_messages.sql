CREATE TABLE IF NOT EXISTS messages (
    msg_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    timestamp   TIMESTAMP DEFAULT NOW()
);
