"""Orchestrates: scan data/ → profile each file → store → run agent → save report."""
from datetime import datetime
from pathlib import Path

from src.config import MANUFACTURER_DIR, QUOTES_DIR, UPLOADS_DIR, BASE_DIR
from src.db.postgres import get_conn
from src.pipeline._base import SUPPORTED
from src.monitoring.profiler import profile_file
from src.monitoring.store import is_profiled, upsert_profile, load_all_profiles
from src.monitoring.agent import run_agent

REPORTS_DIR = BASE_DIR / "reports"

DIRECTORIES = {
    "manufacturers_vs":    MANUFACTURER_DIR,
    "quotes_vs":           QUOTES_DIR,
    "client_requests_vs":  UPLOADS_DIR,
}


def run():
    print("Running data profiling …")
    conn = get_conn()
    new_count = 0

    for collection, directory in DIRECTORIES.items():
        if not directory.exists():
            print(f"  Skipping (not found): {directory.name}/")
            continue
        files = [f for f in directory.rglob("*") if f.suffix.lower() in SUPPORTED]
        print(f"  {collection}: {len(files)} file(s)")

        for path in files:
            from src.pipeline._base import file_hash as compute_hash
            fhash = compute_hash(path)
            if is_profiled(conn, path.name, collection, fhash):
                print(f"    Skipping (unchanged): {path.name}")
                continue
            print(f"    Profiling: {path.name}")
            profile = profile_file(path, collection)
            upsert_profile(conn, profile)
            print(f"    ✓ {profile['num_pages'] or '-'} pages, {profile['num_tokens']} tokens")
            new_count += 1

    if new_count == 0:
        print("  All files already profiled — no changes detected.")

    print("\nRunning report agent …")
    profiles = load_all_profiles(conn)
    conn.close()

    report = run_agent(profiles)

    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"data_profile_{timestamp}.md"
    report_path.write_text(report)
    print(f"  Report saved → {report_path.relative_to(BASE_DIR)}")
