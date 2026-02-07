"""
RAG: Ingest (PDF → Chroma), Chat (Frage mit Kontext + Citations), Docs-Verwaltung.
"""
import io
import logging
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_api_key
from app.core.config import settings
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    Citation,
    IngestResponse,
)
from app.services.embeddings import embed_documents, embed_query, is_loaded
from app.services.llm_client import LLMClient
from app.services.vector_store import (
    add_chunks,
    chroma_reachable,
    collection_count,
    delete_by_doc_id,
    get_collection,
    query_chunks,
)
from app.utils.chunking import chunk_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"], dependencies=[Depends(require_api_key)])
llm_client = LLMClient()

MAX_BYTES = (settings.MAX_UPLOAD_MB or 50) * 1024 * 1024
RAG_TOP_K = settings.RAG_TOP_K
RAG_MAX_CONTEXT_CHARS = settings.RAG_MAX_CONTEXT_CHARS
RAG_MAX_CHUNKS = getattr(settings, "RAG_MAX_CHUNKS_PER_INGEST", 2000)


def _extract_text_from_pdf(content: bytes):
    # -> (page_texts: list, warnings: list)
    """Liefert (page_texts, warnings). Leere Seiten → Warning."""
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        raise ValueError("pypdf nicht installiert. Bitte installieren: pip install pypdf") from None
    warnings = []
    page_texts = []
    try:
        reader = PdfReader(io.BytesIO(content))
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
                page_texts.append(t)
                if not t.strip():
                    warnings.append(f"Seite {i + 1} leer (evtl. Scan-PDF)")
            except Exception as e:
                warnings.append(f"Seite {i + 1}: {str(e)}")
    except Exception as e:
        raise ValueError(f"PDF konnte nicht gelesen werden: {e}") from e
    return page_texts, warnings


def _chunk_pages_with_metadata(
    page_texts: list,
    doc_id: str,
    filename: str,
):
    """Chunk pro Seite, ids und metadatas inkl. page."""
    all_ids: list[str] = []
    all_docs: list[str] = []
    all_metadatas: list[dict] = []
    for page_no, text in enumerate(page_texts):
        if not text.strip():
            continue
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        for idx, chunk in enumerate(chunks):
            cid = f"{doc_id}:{page_no + 1}:{idx}"
            all_ids.append(cid)
            all_docs.append(chunk)
            all_metadatas.append({
                "doc_id": doc_id,
                "filename": filename,
                "page": page_no + 1,
                "chunk_index": idx,
            })
    return all_ids, all_docs, all_metadatas


@router.post("/ingest", response_model=IngestResponse)
async def ingest(file: UploadFile = File(...)):
    """PDF hochladen → Text extrahieren, chunken, embedden, in Chroma speichern."""
    filename = file.filename or "document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien erlaubt.")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Datei zu groß. Max {settings.MAX_UPLOAD_MB} MB.",
        )

    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma nicht erreichbar.")

    if not is_loaded():
        raise HTTPException(status_code=500, detail="Embedding-Modell noch nicht geladen.")

    doc_id = uuid.uuid4().hex

    try:
        page_texts, warnings = _extract_text_from_pdf(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not page_texts or not any(t.strip() for t in page_texts):
        return IngestResponse(
            doc_id=doc_id,
            filename=filename,
            chunks=0,
            pages=0,
            collection=settings.CHROMA_COLLECTION,
            status="skipped",
            warnings=["Kein Text extrahiert (evtl. Scan-PDF)."] + warnings,
        )

    ids, documents, metadatas = _chunk_pages_with_metadata(page_texts, doc_id, filename)
    if not ids:
        return IngestResponse(
            doc_id=doc_id,
            filename=filename,
            chunks=0,
            pages=len(page_texts),
            collection=settings.CHROMA_COLLECTION,
            status="skipped",
            warnings=warnings,
        )

    if len(ids) > RAG_MAX_CHUNKS:
        warnings.append(f"Nur erste {RAG_MAX_CHUNKS} Chunks indexiert (Limit).")
        ids, documents, metadatas = ids[:RAG_MAX_CHUNKS], documents[:RAG_MAX_CHUNKS], metadatas[:RAG_MAX_CHUNKS]

    try:
        embeddings = embed_documents(documents)
    except Exception as e:
        logger.exception("Embedding fehlgeschlagen")
        raise HTTPException(status_code=500, detail=f"Embedding fehlgeschlagen: {e}") from e

    try:
        add_chunks(doc_id=doc_id, filename=filename, ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    except Exception as e:
        logger.exception("Chroma add fehlgeschlagen")
        raise HTTPException(status_code=503, detail=f"Chroma speichern fehlgeschlagen: {e}") from e

    return IngestResponse(
        doc_id=doc_id,
        filename=filename,
        chunks=len(ids),
        pages=len(page_texts),
        collection=settings.CHROMA_COLLECTION,
        status="indexed",
        warnings=warnings,
    )


def _build_rag_prompt(context: str, question: str, language: str) -> str:
    lang_instruction = "Antworte auf Deutsch." if language == "de" else "Answer in English."
    return f"""Antworte ausschließlich auf Basis des folgenden Kontexts. {lang_instruction}
Wenn die Antwort nicht im Kontext steht, antworte nur: "Nicht im Dokument."

Kontext:
{context}

Frage: {question}

Kurze, sachliche Antwort (nur aus dem Kontext):"""


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Frage an die indexierten Dokumente; Antwort nur aus Kontext + Citations."""
    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma nicht erreichbar.")
    if not is_loaded():
        raise HTTPException(status_code=500, detail="Embedding-Modell noch nicht geladen.")

    top_k = req.top_k or RAG_TOP_K
    try:
        query_emb = embed_query(req.question)
    except Exception as e:
        logger.exception("embed_query failed")
        raise HTTPException(status_code=500, detail=f"Embedding fehlgeschlagen: {e}") from e

    try:
        result = query_chunks(
            query_embedding=query_emb,
            n_results=top_k,
            doc_id=req.doc_id,
        )
    except Exception as e:
        logger.exception("Chroma query failed")
        raise HTTPException(status_code=503, detail=f"Chroma-Anfrage fehlgeschlagen: {e}") from e

    ids = result["ids"]
    documents = result["documents"]
    metadatas = result["metadatas"]
    distances = result["distances"]

    if not documents:
        return ChatResponse(
            answer="Nicht im Dokument.",
            citations=[],
            used_chunks=0,
            doc_id=req.doc_id,
            collection=settings.CHROMA_COLLECTION,
            context_preview=None if not req.return_context else "(kein Kontext)",
        )

    # Kontext bis RAG_MAX_CONTEXT_CHARS bauen
    context_parts = []
    total_len = 0
    for i, doc in enumerate(documents):
        if total_len >= RAG_MAX_CONTEXT_CHARS:
            break
        part = doc if isinstance(doc, str) else str(doc)
        if total_len + len(part) > RAG_MAX_CONTEXT_CHARS:
            part = part[: RAG_MAX_CONTEXT_CHARS - total_len]
        context_parts.append(part)
        total_len += len(part)
    context = "\n\n---\n\n".join(context_parts)

    prompt = _build_rag_prompt(context, req.question, req.language)
    try:
        answer = await llm_client.completion(prompt, n_predict=800, temperature=0.2)
        answer = (answer or "").strip()
        if not answer:
            answer = "Nicht im Dokument."
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=502, detail=f"LLM nicht erreichbar: {e}") from e

    # Citations aus Treffern (Chroma distances: kleiner = ähnlicher)
    citations = []
    for i, (cid, meta, dist, doc_text) in enumerate(zip(ids, metadatas or [], distances or [], documents)):
        meta = meta or {}
        excerpt = (doc_text or "")[:400] + ("..." if len(doc_text or "") > 400 else "")
        score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
        citations.append(Citation(
            chunk_id=cid,
            filename=meta.get("filename", ""),
            page=meta.get("page"),
            score=round(score, 4),
            excerpt=excerpt,
        ))

    return ChatResponse(
        answer=answer,
        citations=citations,
        used_chunks=len(documents),
        doc_id=req.doc_id,
        collection=settings.CHROMA_COLLECTION,
        context_preview=context[:500] + "..." if req.return_context and context else None,
    )


@router.get("/docs")
async def list_docs():
    """Collection-Info: Name und Anzahl Chunks (für Tests/Debug)."""
    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma nicht erreichbar.")
    return {
        "collection": settings.CHROMA_COLLECTION,
        "total_chunks": collection_count(),
    }


@router.delete("/docs/{doc_id}")
async def delete_doc(doc_id: str):
    """Alle Chunks mit doc_id löschen (für Tests / Reset)."""
    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma nicht erreichbar.")
    try:
        delete_by_doc_id(doc_id)
    except Exception as e:
        logger.exception("Delete doc_id=%s failed", doc_id)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "deleted", "doc_id": doc_id}
