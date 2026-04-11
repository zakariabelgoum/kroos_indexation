"""Shared helpers for all index pipelines."""
import hashlib
from pathlib import Path

import psycopg2
from qdrant_client import QdrantClient

from src.parsers.pdf import parse_pdf
from src.parsers.excel import parse_excel
from src.parsers.word import parse_word
from src.processing.chunker import chunk
from src.processing.embedder import embed

SUPPORTED = {".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx"}


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def parse(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    if ext in {".xlsx", ".xls", ".csv"}:
        return parse_excel(path)
    if ext in {".doc", ".docx"}:
        return parse_word(path)
    return ""


def is_indexed(conn, filename: str, collection: str, fhash: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT file_hash FROM indexed_files WHERE filename = %s AND collection = %s",
        (filename, collection),
    )
    row = cur.fetchone()
    cur.close()
    return row is not None and row[0] == fhash


def mark_indexed(conn, filename: str, collection: str, fhash: str):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO indexed_files (filename, collection, file_hash)
        VALUES (%s, %s, %s)
        ON CONFLICT (filename, collection)
        DO UPDATE SET file_hash = EXCLUDED.file_hash, indexed_at = NOW()
        """,
        (filename, collection, fhash),
    )
    conn.commit()
    cur.close()


def index_directory(
    directory: Path,
    collection: str,
    upsert_fn,
    conn,
    qdrant: QdrantClient,
):
    if not directory.exists():
        print(f"  Directory not found: {directory}")
        return

    files = [f for f in directory.rglob("*") if f.suffix.lower() in SUPPORTED]
    print(f"  Found {len(files)} file(s) in {directory.name}/")

    for path in files:
        fhash = file_hash(path)
        rel = str(path.relative_to(directory))

        if is_indexed(conn, rel, collection, fhash):
            print(f"    Skipping (unchanged): {rel}")
            continue

        print(f"    Indexing: {rel}")
        text = parse(path)
        if not text.strip():
            print(f"    Warning: no text extracted from {rel}")
            continue

        chunks = chunk(text)
        embeddings = embed(chunks)
        upsert_fn(qdrant, rel, chunks, embeddings)
        mark_indexed(conn, rel, collection, fhash)
        print(f"    ✓ {len(chunks)} chunk(s) indexed")
