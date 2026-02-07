"""Einfaches Text-Chunking (ohne LangChain)."""
from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> List[str]:
    """Teilt Text in überlappende Chunks. Leere Chunks werden ausgelassen."""
    if not text or not text.strip():
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Überlappung: nächster Start geht zurück
        start = end - overlap
        if chunk.strip():
            chunks.append(chunk.strip())
    return chunks
