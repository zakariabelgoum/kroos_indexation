from src.config import MANUFACTURER_DIR
from src.db.postgres import get_conn
from src.vector.qdrant import get_client
from src.vector.manufacturers import upsert, COLLECTION
from src.pipeline._base import index_directory


def run():
    print("Indexing manufacturers …")
    conn = get_conn()
    qdrant = get_client()
    index_directory(MANUFACTURER_DIR, COLLECTION, upsert, conn, qdrant)
    conn.close()
    print("Done.\n")
