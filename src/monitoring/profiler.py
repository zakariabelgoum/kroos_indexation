"""Extract metadata from a single file: pages, tokens, size, type."""
import os
import tiktoken
import pdfplumber
from pathlib import Path

from src.pipeline._base import parse, file_hash

_tokenizer = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_tokenizer.encode(text))


def count_words(text: str) -> int:
    return len(text.split()) if text else 0


def count_pages(path: Path) -> int | None:
    if path.suffix.lower() == ".pdf":
        try:
            with pdfplumber.open(path) as pdf:
                return len(pdf.pages)
        except Exception:
            return None
    return None  # not applicable for Excel/Word


def profile_file(path: Path, collection: str) -> dict:
    text = parse(path)
    return {
        "filename":        path.name,
        "collection":      collection,
        "file_type":       path.suffix.lower().lstrip("."),
        "file_size_bytes": os.path.getsize(path),
        "num_pages":       count_pages(path),
        "num_words":       count_words(text),
        "num_tokens":      count_tokens(text) if text else 0,
        "file_hash":       file_hash(path),
    }
