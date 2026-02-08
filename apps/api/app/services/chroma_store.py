"""
Chroma-Store: Client, Collection, Upsert, Delete.
Single Source für Ingest; Router gibt bei Fehlern 503 (Chroma unreachable).
"""
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings


class ChromaUnavailableError(RuntimeError):
    """Chroma ist nicht erreichbar → Router soll 503 zurückgeben."""
    pass


def get_client():
    """Chroma HTTP-Client (Host/Port aus Settings)."""
    settings = get_settings()
    try:
        return chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
    except Exception as e:
        raise ChromaUnavailableError(str(e)) from e


def get_collection(name: Optional[str] = None) -> Collection:
    """Collection holen oder anlegen (Default: CHROMA_COLLECTION aus Settings)."""
    settings = get_settings()
    coll_name = name or settings.CHROMA_COLLECTION
    client = get_client()
    try:
        return client.get_or_create_collection(name=coll_name, metadata={"description": "PDF chunks for RAG"})
    except Exception as e:
        raise RuntimeError(f"Failed to get/create collection '{coll_name}': {e}") from e


def upsert_chunks(
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    collection_name: Optional[str] = None,
) -> None:
    """Chunks in Chroma upserten (ids, embeddings, documents, metadatas – nur JSON-serializable)."""
    col = get_collection(collection_name)
    try:
        col.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    except Exception as e:
        raise RuntimeError(f"Chroma upsert failed: {e}") from e


def delete_by_doc_id(doc_id: str, collection_name: Optional[str] = None) -> None:
    """Alle Chunks mit doc_id löschen."""
    col = get_collection(collection_name)
    try:
        col.delete(where={"doc_id": doc_id})
    except Exception as e:
        raise RuntimeError(f"Chroma delete failed: {e}") from e
