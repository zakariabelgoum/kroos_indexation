def chunk(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks of `size` characters with `overlap` overlap."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start += size - overlap
    return [c for c in chunks if c]
