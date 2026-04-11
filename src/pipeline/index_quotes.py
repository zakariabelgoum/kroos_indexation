from src.config import QUOTES_DIR
from src.db.postgres import get_conn
from src.vector.qdrant import get_client
from src.vector.quotes import upsert, COLLECTION
from src.pipeline._base import index_directory


def run():
    print("Indexing reference quotes …")
    conn = get_conn()
    qdrant = get_client()
    index_directory(QUOTES_DIR, COLLECTION, upsert, conn, qdrant)
    conn.close()
    print("Done.\n")
