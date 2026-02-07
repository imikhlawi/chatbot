"""
Chroma Vector-Store: Verbindung, Collection, Upsert, Query, Delete.
Nutzt chromadb HttpClient (Docker: chroma:8000, lokal: 127.0.0.1:8001).
"""
import logging
import threading
from typing import List, Optional, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def get_chroma_client():
    """Chroma HTTP-Client (Singleton)."""
    global _client
    if _client is None:
        import chromadb
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    return _client


def get_collection():
    """Collection für RAG (pdf_chatbot) holen oder anlegen."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"description": "PDF chunks for RAG"},
    )


def add_chunks(
    doc_id: str,
    filename: str,
    ids: List[str],
    documents: List[str],
    metadatas: List[dict],
    embeddings: List[List[float]],
) -> None:
    """Chunks in Chroma upserten. ids z. B. doc_id:page:chunk_index."""
    coll = get_collection()
    coll.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    logger.info("Ingested doc_id=%s filename=%s chunks=%d", doc_id, filename, len(ids))


def query_chunks(
    query_embedding: List[float],
    n_results: int,
    doc_id: Optional[str] = None,
) -> dict:
    """
    Ähnliche Chunks abfragen.
    Returns: {"ids": [...], "documents": [...], "metadatas": [...], "distances": [...]}
    """
    coll = get_collection()
    where = {"doc_id": doc_id} if doc_id else None
    result = coll.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    # chromadb liefert Listen pro Key; wir haben eine Query
    out = {
        "ids": result["ids"][0] if result["ids"] else [],
        "documents": result["documents"][0] if result["documents"] else [],
        "metadatas": result["metadatas"][0] if result["metadatas"] else [],
        "distances": result["distances"][0] if result["distances"] else [],
    }
    return out


def delete_by_doc_id(doc_id: str) -> None:
    """Alle Chunks mit doc_id löschen."""
    coll = get_collection()
    coll.delete(where={"doc_id": doc_id})
    logger.info("Deleted doc_id=%s", doc_id)


def collection_count() -> int:
    """Anzahl Einträge in der Collection (für Health/Admin)."""
    coll = get_collection()
    return coll.count()


def chroma_reachable(timeout_seconds: float = 5.0) -> bool:
    """Prüft, ob Chroma erreichbar ist (für /health/deps). Mit Timeout, damit die API nicht hängt."""
    result = [False]

    def _check():
        try:
            client = get_chroma_client()
            if hasattr(client, "heartbeat"):
                client.heartbeat()
            else:
                get_collection().count()
            result[0] = True
        except Exception as e:
            logger.debug("Chroma check failed: %s", e)

    t = threading.Thread(target=_check, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)
    return result[0]
