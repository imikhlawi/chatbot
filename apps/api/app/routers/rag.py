"""
RAG: Ingest (PDF → Chroma), Chat (Frage mit Kontext + Citations), Docs-Verwaltung.
Schutzmaßnahmen: Limits, Logging, klare Fehlercodes (400/413/503/500).
"""
import io
import logging
import re
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.core.deps import require_api_key
from app.core.config import get_settings, settings
from app.schemas.rag import (
    ChatRequest,
    ChatResponse,
    Citation,
    IngestResponse,
)
from app.services.embeddings import embed_documents, embed_query, is_loaded
from app.services.llm_client import LLMClient
from app.services.chroma_store import upsert_chunks as chroma_upsert_chunks, ChromaUnavailableError
from app.services.vector_store import (
    chroma_reachable,
    collection_count,
    delete_by_doc_id,
    query_chunks,
)
from app.utils.chunking import chunk_text

logger = logging.getLogger(__name__)
log = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/rag", tags=["rag"], dependencies=[Depends(require_api_key)])
llm_client = LLMClient()

def _sanitize_filename(name: str) -> str:
    """Dateiname für Anzeige sanitizen (nur sichere Zeichen, max 200 Zeichen)."""
    name = name or "file.pdf"
    name = re.sub(r"[^a-zA-Z0-9._ \-]", "_", name)
    return name[:200]


MAX_BYTES = (settings.MAX_UPLOAD_MB or 50) * 1024 * 1024
RAG_TOP_K = settings.RAG_TOP_K
RAG_MAX_CONTEXT_CHARS = settings.RAG_MAX_CONTEXT_CHARS
RAG_MAX_CHUNKS = getattr(settings, "RAG_MAX_CHUNKS", None) or getattr(settings, "RAG_MAX_CHUNKS_PER_INGEST", 5000)
CHUNK_SIZE = getattr(settings, "CHUNK_SIZE", 1000)
CHUNK_OVERLAP = getattr(settings, "CHUNK_OVERLAP", 200)


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
    chunk_size: int,
    chunk_overlap: int,
):
    """Chunk pro Seite, ids und metadatas inkl. page."""
    all_ids: list[str] = []
    all_docs: list[str] = []
    all_metadatas: list[dict] = []
    for page_no, text in enumerate(page_texts):
        if not text.strip():
            continue
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
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
    """PDF hochladen → Text extrahieren, chunken, embedden, in Chroma speichern. Limits + Logging."""
    t0 = time.perf_counter()
    settings = get_settings()
    filename = _sanitize_filename(file.filename)
    if not (file.content_type == "application/pdf" or filename.lower().endswith(".pdf")):
        raise HTTPException(status_code=400, detail="Not a PDF upload.")

    content = await file.read()
    size_bytes = len(content)
    max_bytes = int(settings.MAX_UPLOAD_MB or 50) * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_UPLOAD_MB} MB.")

    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma unreachable")
    if not is_loaded():
        raise HTTPException(status_code=500, detail="Embedding-Modell noch nicht geladen.")

    doc_id = uuid.uuid4().hex

    try:
        page_texts, warnings = _extract_text_from_pdf(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"PDF could not be parsed: {e}")

    def _elapsed() -> int:
        return int(round((time.perf_counter() - t0) * 1000))

    if not page_texts or not any(t.strip() for t in page_texts):
        elapsed_ms = _elapsed()
        log.info(f"[ingest] skipped doc_id={doc_id} file={filename} bytes={size_bytes} pages=0 chunks=0 elapsed_ms={elapsed_ms}")
        return IngestResponse(
            doc_id=doc_id,
            filename=filename,
            bytes=size_bytes,
            pages=0,
            chunks=0,
            collection=settings.CHROMA_COLLECTION,
            status="skipped",
            warnings=["No text extracted (likely a scanned PDF). OCR is not implemented yet."] + warnings,
            elapsed_ms=elapsed_ms,
        )

    ids, documents, metadatas = _chunk_pages_with_metadata(
        page_texts, doc_id, filename, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    if not ids:
        elapsed_ms = _elapsed()
        log.info(f"[ingest] skipped doc_id={doc_id} file={filename} bytes={size_bytes} pages={len(page_texts)} chunks=0 elapsed_ms={elapsed_ms}")
        return IngestResponse(
            doc_id=doc_id,
            filename=filename,
            bytes=size_bytes,
            pages=len(page_texts),
            chunks=0,
            collection=settings.CHROMA_COLLECTION,
            status="skipped",
            warnings=warnings,
            elapsed_ms=elapsed_ms,
        )

    if len(ids) > RAG_MAX_CHUNKS:
        raise HTTPException(
            status_code=413,
            detail=f"Too many chunks (>{RAG_MAX_CHUNKS}). Reduce PDF size or adjust chunking.",
        )

    try:
        embeddings = embed_documents(documents, batch_size=32)
    except Exception as e:
        logger.exception("Embedding fehlgeschlagen")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {e}") from e

    try:
        chroma_upsert_chunks(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    except ChromaUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"Chroma unavailable: {e}") from e
    except Exception as e:
        err_msg = str(e).lower()
        if "dimension" in err_msg or ("embedding" in err_msg and "size" in err_msg):
            raise HTTPException(status_code=500, detail="Dimension mismatch (Embedding-Modell oder Collection geändert?).") from e
        logger.exception("Chroma upsert fehlgeschlagen")
        raise HTTPException(status_code=500, detail=str(e)) from e

    elapsed_ms = _elapsed()
    log.info(f"[ingest] indexed doc_id={doc_id} file={filename} bytes={size_bytes} pages={len(page_texts)} chunks={len(ids)} elapsed_ms={elapsed_ms}")
    return IngestResponse(
        doc_id=doc_id,
        filename=filename,
        bytes=size_bytes,
        pages=len(page_texts),
        chunks=len(ids),
        collection=settings.CHROMA_COLLECTION,
        status="indexed",
        warnings=warnings,
        elapsed_ms=elapsed_ms,
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


async def _stream_rag_chat(req: ChatRequest):
    """Generator: NDJSON lines. First 'meta' (citations, used_chunks), then 'token' lines, then 'done'."""
    import json
    top_k = req.top_k or RAG_TOP_K
    try:
        query_emb = embed_query(req.question)
    except Exception as e:
        logger.exception("embed_query failed")
        yield json.dumps({"type": "error", "detail": f"Embedding fehlgeschlagen: {e}"}) + "\n"
        return
    try:
        result = query_chunks(
            query_embedding=query_emb,
            n_results=top_k,
            doc_id=req.doc_id,
        )
    except Exception as e:
        logger.exception("Chroma query failed")
        yield json.dumps({"type": "error", "detail": f"Chroma-Anfrage fehlgeschlagen: {e}"}) + "\n"
        return
    ids = result["ids"]
    documents = result["documents"]
    metadatas = result["metadatas"]
    distances = result["distances"]
    citations = []
    if documents:
        for cid, meta, dist, doc_text in zip(ids, metadatas or [], distances or [], documents):
            meta = meta or {}
            excerpt = (doc_text or "")[:400] + ("..." if len(doc_text or "") > 400 else "")
            score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
            citations.append({
                "chunk_id": cid,
                "filename": meta.get("filename", ""),
                "page": meta.get("page"),
                "score": round(score, 4),
                "excerpt": excerpt,
            })
    meta_line = {
        "type": "meta",
        "citations": citations,
        "used_chunks": len(documents),
        "doc_id": req.doc_id,
        "collection": settings.CHROMA_COLLECTION,
    }
    yield json.dumps(meta_line) + "\n"
    if not documents:
        yield json.dumps({"type": "token", "content": "Nicht im Dokument."}) + "\n"
        yield json.dumps({"type": "done"}) + "\n"
        return
    context_parts = []
    total_len = 0
    for doc in documents:
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
        async for content in llm_client.completion_stream(prompt, n_predict=800, temperature=0.2):
            if content:
                yield json.dumps({"type": "token", "content": content}) + "\n"
    except Exception as e:
        logger.exception("LLM stream failed")
        yield json.dumps({"type": "error", "detail": str(e)}) + "\n"
        return
    yield json.dumps({"type": "done"}) + "\n"


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """RAG-Chat mit Echtzeit-Streaming: zuerst Meta (Citations), dann Token für die Antwort."""
    if not chroma_reachable():
        raise HTTPException(status_code=503, detail="Chroma nicht erreichbar.")
    if not is_loaded():
        raise HTTPException(status_code=500, detail="Embedding-Modell noch nicht geladen.")
    return StreamingResponse(
        _stream_rag_chat(req),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
