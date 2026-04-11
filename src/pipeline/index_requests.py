from src.config import UPLOADS_DIR
from src.db.postgres import get_conn
from src.vector.qdrant import get_client
from src.vector.client_requests import upsert, COLLECTION
from src.pipeline._base import index_directory


def run():
    print("Indexing client requests …")
    conn = get_conn()
    qdrant = get_client()
    index_directory(UPLOADS_DIR, COLLECTION, upsert, conn, qdrant)
    conn.close()
    print("Done.\n")
