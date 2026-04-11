from pathlib import Path
from src.db.postgres import get_conn

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def run_migrations():
    conn = get_conn()
    cur = conn.cursor()

    # Bootstrap: tracking table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id          SERIAL PRIMARY KEY,
            filename    TEXT UNIQUE NOT NULL,
            applied_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    cur.execute("SELECT filename FROM migrations ORDER BY filename")
    applied = {row[0] for row in cur.fetchall()}

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    new_count = 0
    for path in migration_files:
        if path.name in applied:
            continue
        print(f"  Applying {path.name} …")
        cur.execute(path.read_text())
        cur.execute("INSERT INTO migrations (filename) VALUES (%s)", (path.name,))
        conn.commit()
        print(f"  ✓ {path.name}")
        new_count += 1

    cur.close()
    conn.close()

    if new_count == 0:
        print("  Already up to date.")
    else:
        print(f"  {new_count} migration(s) applied.")
