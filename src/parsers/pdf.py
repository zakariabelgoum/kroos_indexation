import base64
import pdfplumber
from pathlib import Path

_OCR_THRESHOLD = 50

_EXTRACT_PROMPT = """Extract all text from this PDF exactly as it appears.
Output only the raw text content, preserving structure and line breaks.
Do not summarize, interpret, or add anything."""


def parse_pdf(path: Path) -> str:
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    text = "\n\n".join(parts)

    if len(text.strip()) < _OCR_THRESHOLD:
        text = _extract_with_claude(path)

    return text


def _extract_with_claude(path: Path) -> str:
    from anthropic import Anthropic
    from src.config import ANTHROPIC_API_KEY

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    pdf_data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_data},
                    },
                    {"type": "text", "text": _EXTRACT_PROMPT},
                ],
            }
        ],
    )
    return response.content[0].text.strip()
