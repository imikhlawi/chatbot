# PDF-Chatbot API

FastAPI-Backend für RAG (PDF-Ingest, Chat mit Streaming), Briefing und Docs-Verwaltung. Läuft mit lokalem LLM (llama.cpp) und ChromaDB.

## Quick Start (Docker, empfohlen)

Im Projektroot:

```bash
docker compose up -d --build
```

API: **http://localhost:8000**, Swagger: **http://localhost:8000/docs**

## Lokaler Start (ohne Docker)

```bash
cd apps/api
cp .env.example .env
# .env anpassen: LLM_BASE_URL=http://127.0.0.1:8080, CHROMA_HOST=127.0.0.1, CHROMA_PORT=8001
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

LLM und Chroma müssen separat laufen (z. B. Docker nur für llm + chroma).

## Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/health` | Liveness |
| GET | `/health/deps` | LLM-, Chroma-, Embeddings-Status |
| POST | `/api/rag/ingest` | PDF-Upload → Chroma |
| POST | `/api/rag/chat` | RAG-Chat (komplette Antwort) |
| POST | `/api/rag/chat/stream` | RAG-Chat (Echtzeit-Stream) |
| GET | `/api/rag/docs` | Collection + Chunk-Anzahl |
| DELETE | `/api/rag/docs/{doc_id}` | Dokument löschen |
| POST | `/api/text/briefing` | Smart Briefing |

## Konfiguration

`.env` im Ordner `apps/api/` (siehe `.env.example`).

- **LLM:** `LLM_BASE_URL` (lokal `http://127.0.0.1:8080`, Docker `http://llm:8080`)
- **Chroma:** `CHROMA_HOST`, `CHROMA_PORT`, `CHROMA_COLLECTION`
- **RAG:** `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, `MAX_UPLOAD_MB`, `RAG_MAX_CHUNKS`, `CHUNK_SIZE`, `CHUNK_OVERLAP`
- **Optional:** `API_KEY` → dann Header `X-API-Key` bei geschützten Endpoints

## Tests

```bash
python test_api.py
python test_rag.py
python test_rag.py path/to/file.pdf
```
