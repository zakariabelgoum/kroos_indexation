"""Shared helpers for all index pipelines."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from qdrant_client import QdrantClient

from src.parsers.pdf import parse_pdf
from src.parsers.excel import parse_excel
from src.parsers.word import parse_word
from src.processing.chunker import chunk
from src.processing.embedder import embed
from src.vector.collections import upsert
from src.classifier import classify_document, get_collection
from src.config import DATA_DIR, ANTHROPIC_API_KEY, REPORTS_DIR

CLASSIFICATIONS_FILE = REPORTS_DIR / "classifications.json"


def _load_classifications() -> list:
    if CLASSIFICATIONS_FILE.exists():
        return json.loads(CLASSIFICATIONS_FILE.read_text())
    return []


def _save_classification(record: dict):
    REPORTS_DIR.mkdir(exist_ok=True)
    entries = _load_classifications()
    entries = [e for e in entries if e.get("filename") != record["filename"]]
    entries.append(record)
    CLASSIFICATIONS_FILE.write_text(json.dumps(entries, indent=2))

SUPPORTED = {".pdf", ".xlsx", ".xls", ".csv", ".doc", ".docx"}

STATE_FILE = DATA_DIR / ".index_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


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


def is_indexed(filename: str, collection: str, fhash: str) -> bool:
    state = _load_state()
    key = f"{collection}::{filename}"
    return state.get(key) == fhash


def mark_indexed(filename: str, collection: str, fhash: str):
    state = _load_state()
    key = f"{collection}::{filename}"
    state[key] = fhash
    _save_state(state)


def index_directory(directory: Path, qdrant: QdrantClient):
    if not directory.exists():
        print(f"  Directory not found: {directory}")
        return

    files = [f for f in directory.rglob("*") if f.suffix.lower() in SUPPORTED]
    print(f"  Found {len(files)} file(s) in {directory.name}/")

    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

    for path in files:
        fhash = file_hash(path)
        rel = str(path.relative_to(directory))

        # Classify first to determine collection
        print(f"    Classifying: {rel}")
        result = classify_document(anthropic, path)
        category = result.get("category", "unknown")
        collection = get_collection(category)

        if collection is None:
            print(f"    Skipping (unknown category): {rel}")
            _save_classification({
                "filename":      rel,
                "category":      category,
                "confidence":    result.get("confidence", ""),
                "reason":        result.get("reason", ""),
                "classified_by": result.get("classified_by", ""),
                "collection":    None,
                "indexed_at":    datetime.utcnow().isoformat(),
            })
            continue

        print(f"    → {category} ({result.get('confidence', '?')}) → {collection}")

        _save_classification({
            "filename":      rel,
            "category":      category,
            "confidence":    result.get("confidence", ""),
            "reason":        result.get("reason", ""),
            "classified_by": result.get("classified_by", ""),
            "collection":    collection,
            "indexed_at":    datetime.utcnow().isoformat(),
        })

        if is_indexed(rel, collection, fhash):
            print(f"    Skipping (unchanged): {rel}")
            continue

        text = parse(path)
        if not text.strip():
            print(f"    Warning: no text extracted from {rel}")
            continue

        chunks = chunk(text)
        embeddings = embed(chunks)
        upsert(qdrant, collection, rel, chunks, embeddings)
        mark_indexed(rel, collection, fhash)
        print(f"    ✓ {len(chunks)} chunk(s) indexed into {collection}")
