"""
Singleton Embeddings-Service (sentence-transformers).
Einmal beim Startup laden, dann embed_documents / embed_query nutzen.
"""
from typing import List

_embeddings = None


def _ensure_nltk() -> None:
    """NLTK vor sentence-transformers laden, sonst nltk-Fehler."""
    import nltk
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)


def get_embeddings():
    """Liefert das globale Embedding-Modell (lazy load beim ersten Aufruf)."""
    global _embeddings
    if _embeddings is None:
        _ensure_nltk()
        from sentence_transformers import SentenceTransformer
        _embeddings = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embedding-Vektoren für eine Liste von Texten (z. B. Chunks)."""
    if not texts:
        return []
    model = get_embeddings()
    return model.encode(texts, convert_to_numpy=True).tolist()


def embed_query(text: str) -> List[float]:
    """Embedding-Vektor für eine einzelne Query."""
    model = get_embeddings()
    return model.encode(text, convert_to_numpy=True).tolist()


def is_loaded() -> bool:
    """True, wenn das Modell bereits geladen wurde."""
    return _embeddings is not None
