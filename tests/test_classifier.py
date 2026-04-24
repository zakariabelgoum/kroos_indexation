import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.classifier import _parse_response, extract_text, get_collection, classify_document


# --- _parse_response ---

def test_parse_response_plain_json():
    raw = json.dumps({"filename": "doc.pdf", "category": "catalogue", "confidence": "high", "reason": "test"})
    result = _parse_response(raw)
    assert result["category"] == "catalogue"
    assert result["confidence"] == "high"


def test_parse_response_strips_code_fence():
    raw = "```json\n{\"filename\": \"doc.pdf\", \"category\": \"quotes\", \"confidence\": \"medium\", \"reason\": \"x\"}\n```"
    result = _parse_response(raw)
    assert result["category"] == "quotes"


def test_parse_response_adds_defaults():
    raw = json.dumps({"filename": "doc.pdf", "category": "prices"})
    result = _parse_response(raw)
    assert result["confidence"] == "medium"
    assert result["reason"] == ""


def test_parse_response_invalid_json_raises():
    with pytest.raises(Exception):
        _parse_response("not valid json")


# --- get_collection ---

def test_get_collection_known_categories():
    assert get_collection("catalogue") == "catalogue_vs"
    assert get_collection("fiche_technique") == "fiche_technique_vs"
    assert get_collection("request") == "request_vs"
    assert get_collection("quotes") == "quotes_vs"
    assert get_collection("prices") == "prices_vs"
    assert get_collection("discount") == "discount_vs"


def test_get_collection_unknown_returns_none():
    assert get_collection("unknown") is None
    assert get_collection("garbage") is None


# --- extract_text ---

def test_extract_text_reads_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    assert extract_text(f) == "hello world"


def test_extract_text_strips_whitespace(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("  hello  \n")
    assert extract_text(f) == "hello"


def test_extract_text_missing_file_returns_error_string(tmp_path):
    f = tmp_path / "nonexistent.txt"
    result = extract_text(f)
    assert "Error" in result


# --- classify_document ---

def _mock_client(category="catalogue", confidence="high", reason="test"):
    response_text = json.dumps({
        "filename": "doc.pdf",
        "category": category,
        "confidence": confidence,
        "reason": reason,
    })
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    client = MagicMock()
    client.messages.create.return_value = mock_msg
    return client


def test_classify_document_returns_by_title_on_high_confidence(tmp_path):
    f = tmp_path / "catalogue_acme.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    client = _mock_client(category="catalogue", confidence="high")
    result = classify_document(client, f)
    assert result["category"] == "catalogue"
    assert result["classified_by"] == "title"
    assert client.messages.create.call_count == 1


def test_classify_document_falls_back_to_content_on_unknown(tmp_path):
    f = tmp_path / "document.txt"
    f.write_text("This is a price list with discounts.")

    call_count = 0
    def side_effect(**kwargs):
        nonlocal call_count
        call_count += 1
        category = "unknown" if call_count == 1 else "prices"
        confidence = "low" if call_count == 1 else "high"
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps({
            "filename": f.name, "category": category,
            "confidence": confidence, "reason": "test"
        }))]
        return mock_msg

    client = MagicMock()
    client.messages.create.side_effect = side_effect

    result = classify_document(client, f)
    assert result["category"] == "prices"
    assert result["classified_by"] == "content (text)"
    assert client.messages.create.call_count == 2


def test_classify_document_empty_text_file_returns_unknown(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")

    client = _mock_client(category="unknown", confidence="low")
    result = classify_document(client, f)
    assert result["category"] == "unknown"
