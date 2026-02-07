"""
Diagnose-Endpoint: LLM, Chroma (und später Embeddings) erreichbar?
Ermöglicht schnelles Debuggen ohne Raten.
"""
import httpx
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["deps"])


@router.get("/health/deps")
async def health_deps():
    settings = get_settings()

    # 1) LLM prüfen (llama.cpp server: GET / oder /health, je nach Version)
    llm_status = {"status": "down"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            url = settings.LLM_BASE_URL.rstrip("/")
            r = await client.get(f"{url}/")
            if r.status_code in (200, 404):
                llm_status = {"status": "ok", "code": r.status_code}
            else:
                llm_status = {"status": "down", "code": r.status_code}
    except Exception as e:
        llm_status = {"status": "down", "error": str(e)}

    # 2) Chroma prüfen (Heartbeat-Pfad variiert je nach Chroma-Version)
    chroma_status = {"status": "down"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            base = f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
            for path in ("/api/v1/heartbeat", "/api/v1", "/"):
                try:
                    r = await client.get(f"{base}{path}")
                    if r.status_code in (200, 404):
                        chroma_status = {"status": "ok"}
                        break
                except Exception:
                    continue
            if chroma_status["status"] == "down":
                chroma_status["error"] = "kein gültiger Response von Chroma"
    except Exception as e:
        chroma_status = {"status": "down", "error": str(e)}

    return {
        "status": "ok",
        "llm": llm_status,
        "chroma": chroma_status,
        "embeddings": {"status": "todo"},
        "collection": settings.CHROMA_COLLECTION,
    }
