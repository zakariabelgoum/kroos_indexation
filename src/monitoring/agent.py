"""LLM agent that reads document profiles and produces a markdown report."""
import os
import anthropic

_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM = """
You are a data quality analyst for Kroos, a construction products supplier.
You receive a list of document profiles (filename, collection, pages, tokens, size)
and produce a concise markdown report covering:
- Summary table of all documents
- Total tokens and size per collection
- Quality warnings (e.g. empty files, unusually large/small token counts)
- Coverage gaps (e.g. missing price books, no reference quotes)
- Recommendations

Be concise and direct. Use markdown tables and bullet lists.
"""


def run_agent(profiles: list[dict]) -> str:
    if not profiles:
        return "# Data Profile Report\n\nNo documents found in data/.\n"

    profile_text = _build_profile_text(profiles)

    response = _client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": profile_text}],
    )
    return response.content[0].text


def _build_profile_text(profiles: list[dict]) -> str:
    lines = ["Here are the document profiles:\n"]
    lines.append(
        f"{'Filename':<40} {'Collection':<25} {'Type':<8} {'Pages':>6} {'Tokens':>8} {'Size (KB)':>10}"
    )
    lines.append("-" * 105)
    for p in profiles:
        lines.append(
            f"{p['filename']:<40} {p['collection']:<25} {p['file_type']:<8} "
            f"{str(p['num_pages'] or '-'):>6} {p['num_tokens']:>8} "
            f"{p['file_size_bytes'] // 1024:>10}"
        )
    return "\n".join(lines)
