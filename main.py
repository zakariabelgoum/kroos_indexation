import sys


def cmd_migrate():
    from src.db.migrate import run_migrations
    print("Running migrations …")
    run_migrations()


def cmd_init():
    from src.vector.qdrant import get_client, init_collections
    print("Initializing Qdrant collections …")
    init_collections(get_client())


def cmd_index():
    from src.pipeline.index_manufacturers import run as index_manufacturers
    from src.pipeline.index_quotes import run as index_quotes
    from src.pipeline.index_requests import run as index_requests
    index_manufacturers()
    index_quotes()
    index_requests()


def cmd_profile():
    from src.monitoring.run import run
    run()


def cmd_summary():
    from src.monitoring.summary import run
    run()


def cmd_watch():
    import time
    import schedule
    print("Starting watcher (runs every 30 min) …")
    cmd_index()  # run once immediately
    schedule.every(30).minutes.do(cmd_index)
    while True:
        schedule.run_pending()
        time.sleep(60)


COMMANDS = {
    "migrate": cmd_migrate,
    "init":    cmd_init,
    "index":   cmd_index,
    "profile": cmd_profile,
    "summary": cmd_summary,
    "watch":   cmd_watch,
}

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    if command in COMMANDS:
        COMMANDS[command]()
    else:
        print("Usage: python main.py [migrate|init|index|profile|summary|watch]")
        print()
        print("  migrate  — apply pending SQL migrations to Postgres")
        print("  init     — create Qdrant collections if they don't exist")
        print("  index    — index all files in data/ into Qdrant")
        print("  profile  — profile all files and generate an AI report (uses Claude)")
        print("  summary  — static summary: pages, words, tokens per document, no LLM")
        print("  watch    — index once then re-index every 30 minutes")
