import json
import pytest
from pathlib import Path
from unittest.mock import patch
from src.pipeline._base import file_hash, parse, is_indexed, mark_indexed, count_tokens


# --- file_hash ---

def test_file_hash_returns_md5_string(tmp_path):
    f = tmp_path / "test.txt"
    f.write_bytes(b"hello")
    result = file_hash(f)
    assert isinstance(result, str)
    assert len(result) == 32


def test_file_hash_same_content_same_hash(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"same content")
    b.write_bytes(b"same content")
    assert file_hash(a) == file_hash(b)


def test_file_hash_different_content_different_hash(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"content A")
    b.write_bytes(b"content B")
    assert file_hash(a) != file_hash(b)


# --- parse ---

def test_parse_unsupported_extension_returns_empty(tmp_path):
    f = tmp_path / "file.xyz"
    f.write_text("data")
    assert parse(f) == ""


def test_parse_routes_pdf(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4")
    with patch("src.pipeline._base.parse_pdf", return_value="pdf text") as mock:
        result = parse(f)
    mock.assert_called_once_with(f)
    assert result == "pdf text"


def test_parse_routes_excel(tmp_path):
    f = tmp_path / "sheet.xlsx"
    f.write_bytes(b"fake xlsx")
    with patch("src.pipeline._base.parse_excel", return_value="excel text") as mock:
        result = parse(f)
    mock.assert_called_once_with(f)
    assert result == "excel text"


def test_parse_routes_word(tmp_path):
    f = tmp_path / "doc.docx"
    f.write_bytes(b"fake docx")
    with patch("src.pipeline._base.parse_word", return_value="word text") as mock:
        result = parse(f)
    mock.assert_called_once_with(f)
    assert result == "word text"


def test_parse_routes_csv(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b,c")
    with patch("src.pipeline._base.parse_excel", return_value="csv text") as mock:
        result = parse(f)
    mock.assert_called_once_with(f)
    assert result == "csv text"


# --- count_tokens ---

def test_count_tokens_empty():
    assert count_tokens("") == 0


def test_count_tokens_returns_int():
    assert isinstance(count_tokens("hello world"), int)


def test_count_tokens_more_text_more_tokens():
    assert count_tokens("hello world foo bar") > count_tokens("hello")


# --- is_indexed / mark_indexed ---

def test_is_indexed_returns_false_when_no_state(tmp_path):
    with patch("src.pipeline._base.STATE_FILE", tmp_path / ".index_state.json"):
        assert is_indexed("file.pdf", "catalogue_vs", "abc123") is False


def test_mark_indexed_then_is_indexed_true(tmp_path):
    state_file = tmp_path / ".index_state.json"
    with patch("src.pipeline._base.STATE_FILE", state_file):
        mark_indexed("file.pdf", "catalogue_vs", "abc123")
        assert is_indexed("file.pdf", "catalogue_vs", "abc123") is True


def test_is_indexed_false_when_hash_differs(tmp_path):
    state_file = tmp_path / ".index_state.json"
    with patch("src.pipeline._base.STATE_FILE", state_file):
        mark_indexed("file.pdf", "catalogue_vs", "abc123")
        assert is_indexed("file.pdf", "catalogue_vs", "different_hash") is False


def test_mark_indexed_overwrites_old_hash(tmp_path):
    state_file = tmp_path / ".index_state.json"
    with patch("src.pipeline._base.STATE_FILE", state_file):
        mark_indexed("file.pdf", "catalogue_vs", "old_hash")
        mark_indexed("file.pdf", "catalogue_vs", "new_hash")
        assert is_indexed("file.pdf", "catalogue_vs", "new_hash") is True
        assert is_indexed("file.pdf", "catalogue_vs", "old_hash") is False
