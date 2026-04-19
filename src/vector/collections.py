import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


def upsert(client: QdrantClient, collection: str, filename: str, chunks: list[str], embeddings: list[list[float]]):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"filename": filename, "chunk": chunk},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    client.upsert(collection_name=collection, points=points)
