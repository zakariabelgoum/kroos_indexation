import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

COLLECTION = "client_requests_vs"


def upsert(client: QdrantClient, filename: str, chunks: list[str], embeddings: list[list[float]]):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"filename": filename, "chunk": chunk},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=COLLECTION, points=points)


def search(client: QdrantClient, query_vector: list[float], top_k: int = 5) -> list[dict]:
    results = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
    )
    return [
        {"chunk": r.payload["chunk"], "filename": r.payload["filename"], "score": r.score}
        for r in results
    ]
