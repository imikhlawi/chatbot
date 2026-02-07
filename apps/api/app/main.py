from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.health import router as health_router
from app.routers.deps import router as deps_router
from app.routers.text import router as text_router

# RAG optional: App startet auch ohne RAG-Deps (chromadb, pypdf, python-multipart, …)
try:
    from app.routers.rag import router as rag_router
    _rag_available = True
except (ImportError, RuntimeError):
    rag_router = None
    _rag_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: Embedding-Modell laden (einmalig), nur wenn RAG verfügbar."""
    if _rag_available:
        try:
            from app.services import embeddings as emb
            emb.get_embeddings()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Embeddings beim Start nicht geladen: %s", e)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/")
def root():
    info = {
        "app": settings.APP_NAME,
        "docs": "/docs",
        "health": "/health",
        "health_deps": "/health/deps",
        "briefing": "POST /api/text/briefing",
    }
    if _rag_available:
        info["rag_ingest"] = "POST /api/rag/ingest"
        info["rag_chat"] = "POST /api/rag/chat"
        info["rag_docs"] = "GET /api/rag/docs"
        info["rag_delete"] = "DELETE /api/rag/docs/{doc_id}"
    return info

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(deps_router)
app.include_router(text_router)
if rag_router is not None:
    app.include_router(rag_router)
