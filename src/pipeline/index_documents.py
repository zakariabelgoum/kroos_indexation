from src.config import DATA_DIR
from src.vector.qdrant import get_client
from src.pipeline._base import index_directory


def run():
    print("Indexing documents …")
    qdrant = get_client()
    index_directory(DATA_DIR, qdrant)
    print("Done.\n")
