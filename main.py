import sys


def cmd_init():
    from src.vector.qdrant import get_client, init_collections
    print("Initializing Qdrant collections …")
    init_collections(get_client())


def cmd_index():
    from src.pipeline.index_documents import run as index_documents
    index_documents()


def cmd_stats():
    from src.monitoring.stats_agent import run
    print("Generating statistics report …")
    run()


def cmd_watch():
    import time
    import schedule
    print("Starting watcher (runs every 30 min) …")
    cmd_index()
    schedule.every(30).minutes.do(cmd_index)
    while True:
        schedule.run_pending()
        time.sleep(60)


COMMANDS = {
    "init":  cmd_init,
    "index": cmd_index,
    "stats": cmd_stats,
    "watch": cmd_watch,
}

if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    if command in COMMANDS:
        COMMANDS[command]()
    else:
        print("Usage: python main.py [init|index|stats|watch]")
        print()
        print("  init   — create Qdrant collections if they don't exist")
        print("  index  — index all files in data/ into Qdrant")
        print("  stats  — generate descriptive statistics from classifications")
        print("  watch  — index once then re-index every 30 minutes")
