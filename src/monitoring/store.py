"""Persist and retrieve document profiles from Postgres."""
from src.db.postgres import get_conn


def is_profiled(conn, filename: str, collection: str, file_hash: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT file_hash FROM document_profiles WHERE filename = %s AND collection = %s",
        (filename, collection),
    )
    row = cur.fetchone()
    cur.close()
    return row is not None and row[0] == file_hash


def upsert_profile(conn, profile: dict):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO document_profiles
            (filename, collection, file_type, file_size_bytes, num_pages, num_words, num_tokens, file_hash)
        VALUES (%(filename)s, %(collection)s, %(file_type)s, %(file_size_bytes)s,
                %(num_pages)s, %(num_words)s, %(num_tokens)s, %(file_hash)s)
        ON CONFLICT (filename, collection)
        DO UPDATE SET
            file_type       = EXCLUDED.file_type,
            file_size_bytes = EXCLUDED.file_size_bytes,
            num_pages       = EXCLUDED.num_pages,
            num_words       = EXCLUDED.num_words,
            num_tokens      = EXCLUDED.num_tokens,
            file_hash       = EXCLUDED.file_hash,
            profiled_at     = NOW()
        """,
        profile,
    )
    conn.commit()
    cur.close()


def load_all_profiles(conn) -> list[dict]:
    cur = conn.cursor()
    cur.execute("""
        SELECT filename, collection, file_type, file_size_bytes, num_pages, num_words, num_tokens, profiled_at
        FROM document_profiles
        ORDER BY collection, filename
    """)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return rows
