from openai import OpenAI
from src.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def embed(chunks: list[str]) -> list[list[float]]:
    """Embed a list of text chunks. Returns one vector per chunk."""
    if not chunks:
        return []
    results: list[list[float]] = []
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        response = _client.embeddings.create(input=batch, model=MODEL)
        results.extend(e.embedding for e in response.data)
    return results
