import pytest
from src.processing.chunker import chunk


def test_empty_string_returns_empty():
    assert chunk("") == []


def test_whitespace_only_returns_empty():
    assert chunk("   \n  ") == []


def test_short_text_single_chunk():
    result = chunk("hello world", size=800, overlap=100)
    assert result == ["hello world"]


def test_exact_size_single_chunk():
    text = "a" * 800
    result = chunk(text, size=800, overlap=100)
    assert result == [text]


def test_text_longer_than_size_produces_multiple_chunks():
    text = "a" * 1000
    result = chunk(text, size=800, overlap=100)
    assert len(result) == 2


def test_overlap_means_chunks_share_content():
    text = "abcdefghij"
    result = chunk(text, size=6, overlap=2)
    # chunk 1: text[0:6] = "abcdef", chunk 2: text[4:10] = "efghij"
    assert result[0].endswith("ef")
    assert result[1].startswith("ef")


def test_no_empty_chunks_in_output():
    text = "x" * 50
    result = chunk(text, size=10, overlap=5)
    assert all(len(c) > 0 for c in result)


def test_strips_leading_trailing_whitespace():
    result = chunk("  hello  ", size=800, overlap=100)
    assert result == ["hello"]


def test_chunk_size_respected():
    text = "a" * 2000
    result = chunk(text, size=500, overlap=50)
    for c in result:
        assert len(c) <= 500
