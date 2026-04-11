from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from src.config import QDRANT_HOST, QDRANT_PORT, QDRANT_API_KEY

VECTOR_SIZE = 1536  # text-embedding-3-small

COLLECTIONS = [
    "manufacturers_vs",
    "quotes_vs",
    "client_requests_vs",
]


def get_client() -> QdrantClient:
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        api_key=QDRANT_API_KEY or None,
    )


def init_collections(client: QdrantClient):
    existing = {c.name for c in client.get_collections().collections}
    for name in COLLECTIONS:
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"  Created collection: {name}")
        else:
            print(f"  Already exists:     {name}")
