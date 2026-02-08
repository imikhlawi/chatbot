"""
Singleton Embeddings-Service (sentence-transformers).
Thread-safe, einmal laden; embed_documents in Batches, embed_query für Chat.
"""
import threading
from typing import List

from app.core.config import get_settings

_model_lock = threading.Lock()
_model = None


def _ensure_nltk() -> None:
    """NLTK vor sentence-transformers laden, sonst nltk-Fehler."""
    import nltk
    nltk.download("punkt", quiet=True)
    nltk.download("punkt_tab", quiet=True)


def get_embedder():
    """Liefert das globale Embedding-Modell (thread-safe, lazy load). Kein silent None – bei Fehler Exception."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _ensure_nltk()
                from sentence_transformers import SentenceTransformer
                settings = get_settings()
                model_name = getattr(settings, "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
                _model = SentenceTransformer(model_name)
    return _model


def get_embeddings():
    """Alias für Startup/Compat – liefert dasselbe Modell wie get_embedder()."""
    return get_embedder()


def embed_documents(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """Embedding-Vektoren für eine Liste von Texten (z. B. Chunks). Batched für RAM-Schonung.
    Chroma erwartet list[list[float]] – keine PyTorch-Tensoren."""
    if not texts:
        return []
    model = get_embedder()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    # Chroma erwartet list[list[float]] – .tolist() liefert reine Python-Floats
    import numpy as np
    if isinstance(vectors, np.ndarray):
        if vectors.ndim == 1:
            return [vectors.tolist()]
        return vectors.tolist()
    return [[float(x) for x in v] for v in vectors]


def embed_query(text: str) -> List[float]:
    """Embedding-Vektor für eine einzelne Query (z. B. Chat-Frage)."""
    return embed_documents([text], batch_size=1)[0]


def is_loaded() -> bool:
    """True, wenn das Modell bereits geladen wurde."""
    return _model is not None
