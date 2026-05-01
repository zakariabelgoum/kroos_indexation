"""Compute descriptive statistics from classifications.json and save to reports/stats.json."""
import json
from datetime import datetime, UTC
from pathlib import Path

from src.config import REPORTS_DIR

CLASSIFICATIONS_FILE = REPORTS_DIR / "classifications.json"
STATS_FILE           = REPORTS_DIR / "stats.json"


def _stats_for(values: list[int]) -> dict:
    if not values:
        return {"count": 0, "total_tokens": 0, "avg_tokens": 0, "min_tokens": 0, "max_tokens": 0, "std_tokens": 0}
    n      = len(values)
    total  = sum(values)
    avg    = total / n
    min_v  = min(values)
    max_v  = max(values)
    std    = (sum((v - avg) ** 2 for v in values) / n) ** 0.5
    return {
        "count": n,
        "total_tokens": total,
        "avg_tokens":   round(avg, 1),
        "min_tokens":   min_v,
        "max_tokens":   max_v,
        "std_tokens":   round(std, 1),
    }


def run():
    if not CLASSIFICATIONS_FILE.exists():
        print("  No classifications.json found. Run `python main.py index` first.")
        return

    entries = json.loads(CLASSIFICATIONS_FILE.read_text())
    if not entries:
        print("  classifications.json is empty.")
        return

    # --- per-category stats ---
    by_category: dict[str, list] = {}
    for e in entries:
        cat = e.get("category", "unknown")
        by_category.setdefault(cat, []).append(e)

    categories = {}
    for cat, docs in by_category.items():
        tokens = [d["token_count"] for d in docs if d.get("token_count") is not None]
        confidence_dist = {}
        for d in docs:
            c = d.get("confidence", "unknown")
            confidence_dist[c] = confidence_dist.get(c, 0) + 1
        classified_by_dist = {}
        for d in docs:
            cb = d.get("classified_by", "unknown")
            classified_by_dist[cb] = classified_by_dist.get(cb, 0) + 1

        categories[cat] = {
            **_stats_for(tokens),
            "confidence_distribution":    confidence_dist,
            "classified_by_distribution": classified_by_dist,
            "files": [
                {
                    "filename":      d["filename"],
                    "token_count":   d.get("token_count"),
                    "confidence":    d.get("confidence"),
                    "classified_by": d.get("classified_by"),
                    "collection":    d.get("collection"),
                    "indexed_at":    d.get("indexed_at"),
                }
                for d in docs
            ],
        }

    # --- overall stats ---
    all_tokens = [e["token_count"] for e in entries if e.get("token_count") is not None]
    overall = {
        **_stats_for(all_tokens),
        "total_files":        len(entries),
        "categories_found":   list(by_category.keys()),
        "unknown_files":      sum(1 for e in entries if e.get("category") == "unknown"),
        "high_confidence":    sum(1 for e in entries if e.get("confidence") == "high"),
        "medium_confidence":  sum(1 for e in entries if e.get("confidence") == "medium"),
        "low_confidence":     sum(1 for e in entries if e.get("confidence") == "low"),
    }

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "overall":      overall,
        "by_category":  categories,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    STATS_FILE.write_text(json.dumps(report, indent=2))
    print(f"  Stats report saved → {STATS_FILE.relative_to(REPORTS_DIR.parent)}")
