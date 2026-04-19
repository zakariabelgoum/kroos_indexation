import base64
import json
from pathlib import Path
from anthropic import Anthropic

COLLECTION_MAP = {
    "catalogue":       "catalogue_vs",
    "fiche_technique": "fiche_technique_vs",
    "request":         "request_vs",
    "quotes":          "quotes_vs",
    "prices":          "prices_vs",
    "discount":        "discount_vs",
}

CATEGORIES_DESCRIPTION = """
1. catalogue
   Product listings, multiple items, descriptive content, marketing-style info.

2. fiche_technique
   Engineering/technical specifications, tables of characteristics, product performance.

3. request
   Customer inquiries or information requests, often from email text.

4. quotes
   Formal quotations or proposals with pricing breakdowns and terms.

5. prices
   Raw price lists or tables without the structure of a formal quotation.

6. discount
   Promotions, reduced prices, percentage discounts, special offers.
"""

TITLE_SYSTEM_PROMPT = """You are an expert AI document classification agent.

## TASK
Classify a document based ONLY on its filename. Do not invent content.

## CATEGORIES
""" + CATEGORIES_DESCRIPTION + """
## CLASSIFICATION RULES

- If the filename clearly indicates the category, return it with high or medium confidence.
- If the filename is ambiguous, generic, or could belong to multiple categories → return "unknown" with confidence "low".
- Never guess beyond what the filename communicates.

## OUTPUT FORMAT (STRICT JSON ONLY)

{
  "filename": "<file_name>",
  "category": "<one_of_the_6_categories_or_unknown>",
  "confidence": "<low | medium | high>",
  "reason": "<short factual justification>"
}

- Do not output anything other than JSON."""

CONTENT_SYSTEM_PROMPT = """You are an expert AI document classification agent.

## TASK
Classify the document provided (PDF or text). Use all visible content including scanned pages.

## CATEGORIES
""" + CATEGORIES_DESCRIPTION + """
## CLASSIFICATION RULES

- Use semantic understanding, not just keywords.
- If several categories match, choose the most dominant intent.
- If the content is insufficient or ambiguous → return "unknown".
- Stay strict and consistent.

## OUTPUT FORMAT (STRICT JSON ONLY)

{
  "filename": "<file_name>",
  "category": "<one_of_the_6_categories_or_unknown>",
  "confidence": "<low | medium | high>",
  "reason": "<short factual justification>"
}

- Do not hallucinate missing sections.
- Do not output anything other than JSON."""


def _parse_response(raw: str) -> dict:
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    result = json.loads(raw)
    result.setdefault("confidence", "medium")
    result.setdefault("reason", "")
    return result


def _call_claude_text(client: Anthropic, system_prompt: str, user_message: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_message}],
    )
    return _parse_response(response.content[0].text.strip())


def _call_claude_pdf(client: Anthropic, system_prompt: str, filepath: Path) -> dict:
    pdf_data = base64.standard_b64encode(filepath.read_bytes()).decode("utf-8")
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data},
                    },
                    {
                        "type": "text",
                        "text": f"Classify this document (filename: {filepath.name}). Respond ONLY with valid JSON.",
                    },
                ],
            }
        ],
    )
    return _parse_response(response.content[0].text.strip())


def extract_text(filepath: Path) -> str:
    """Extract text from non-PDF files only (PDFs go directly to Claude)."""
    try:
        return filepath.read_text(encoding="utf-8", errors="replace").strip()
    except Exception as e:
        return f"[Error reading file: {e}]"


def classify_document(client: Anthropic, filepath: Path) -> dict:
    # Step 1: try to classify from filename alone
    result = _call_claude_text(
        client,
        TITLE_SYSTEM_PROMPT,
        f"Classify this document based only on its filename. Respond ONLY with valid JSON.\n\nFilename: {filepath.name}",
    )
    result["filename"] = filepath.name

    if result.get("category", "unknown") != "unknown" and result.get("confidence") in ("medium", "high"):
        result["classified_by"] = "title"
        return result

    # Step 2: fall back to content — send PDF natively, read text for other formats
    if filepath.suffix.lower() == ".pdf":
        result = _call_claude_pdf(client, CONTENT_SYSTEM_PROMPT, filepath)
        result["classified_by"] = "content (pdf)"
    else:
        text = extract_text(filepath)
        if not text:
            return {
                "filename": filepath.name,
                "category": "unknown",
                "confidence": "low",
                "reason": "File is empty or could not be read",
                "classified_by": "title",
            }
        result = _call_claude_text(
            client,
            CONTENT_SYSTEM_PROMPT,
            f"Classify the following document. Respond ONLY with valid JSON.\n\nFilename: {filepath.name}\n\nContent:\n{text[:8000]}",
        )
        result["classified_by"] = "content (text)"

    result["filename"] = filepath.name
    return result


def get_collection(category: str) -> str | None:
    """Returns the Qdrant collection name for a category, or None if unknown."""
    return COLLECTION_MAP.get(category)
