"""Static document summary — no LLM. Reads profiles from Postgres and produces a markdown report."""
from datetime import datetime
from pathlib import Path

from src.db.postgres import get_conn
from src.monitoring.store import load_all_profiles
from src.config import BASE_DIR

REPORTS_DIR = BASE_DIR / "reports"

COLLECTION_LABELS = {
    "manufacturers_vs":   "Manufacturer",
    "quotes_vs":          "Reference Quote",
    "client_requests_vs": "Client Request",
}


def run():
    print("Generating static summary …")
    conn = get_conn()
    profiles = load_all_profiles(conn)
    conn.close()

    if not profiles:
        print("  No profiles found. Run `python main.py profile` first.")
        return

    report = _build_report(profiles)

    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = REPORTS_DIR / f"summary_{timestamp}.md"
    path.write_text(report)
    print(f"  Report saved → {path.relative_to(BASE_DIR)}")


def _build_report(profiles: list[dict]) -> str:
    lines = []
    lines.append("# Document Summary\n")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    # Group by collection
    collections: dict[str, list[dict]] = {}
    for p in profiles:
        collections.setdefault(p["collection"], []).append(p)

    for collection, docs in collections.items():
        label = COLLECTION_LABELS.get(collection, collection)
        lines.append(f"\n## {label}\n")

        # Per-document table
        lines.append("| Filename | Type | Pages | Words | Tokens | Size (KB) |")
        lines.append("|----------|------|------:|------:|-------:|----------:|")
        for d in docs:
            pages  = str(d["num_pages"]) if d["num_pages"] is not None else "—"
            words  = f"{d['num_words']:,}"  if d["num_words"]  is not None else "—"
            tokens = f"{d['num_tokens']:,}" if d["num_tokens"] is not None else "—"
            size   = f"{d['file_size_bytes'] // 1024:,}"
            lines.append(
                f"| {d['filename']} | {d['file_type']} | {pages} | {words} | {tokens} | {size} |"
            )

        # Totals for this collection
        total_pages  = sum(d["num_pages"]  or 0 for d in docs)
        total_words  = sum(d["num_words"]  or 0 for d in docs)
        total_tokens = sum(d["num_tokens"] or 0 for d in docs)
        total_size   = sum(d["file_size_bytes"] or 0 for d in docs) // 1024
        lines.append(
            f"| **Total ({len(docs)} files)** | | **{total_pages}** "
            f"| **{total_words:,}** | **{total_tokens:,}** | **{total_size:,}** |"
        )

    # Grand total
    lines.append("\n## Grand Total\n")
    lines.append("| Collection | Files | Pages | Words | Tokens |")
    lines.append("|------------|------:|------:|------:|-------:|")
    for collection, docs in collections.items():
        label  = COLLECTION_LABELS.get(collection, collection)
        pages  = sum(d["num_pages"]  or 0 for d in docs)
        words  = sum(d["num_words"]  or 0 for d in docs)
        tokens = sum(d["num_tokens"] or 0 for d in docs)
        lines.append(f"| {label} | {len(docs)} | {pages} | {words:,} | {tokens:,} |")

    return "\n".join(lines) + "\n"
