# PDF-Chatbot API (Schritt 2)

FastAPI-Backend für Smart Briefing. Läuft lokal, ruft einen **lokalen LLM-Server** (z. B. llama.cpp server) per HTTP auf.

## Start

Aus dem Projektroot (Ordner, in dem `docker-compose.yml` liegt):

```bash
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `GET /health/deps` → Status von LLM, Chroma, Embeddings (für Diagnose)
- `POST /api/text/briefing` → Smart Briefing (JSON)
- **RAG:** `POST /api/rag/ingest` (PDF-Upload), `POST /api/rag/chat`, `GET /api/rag/docs`, `DELETE /api/rag/docs/{doc_id}`

## Konfiguration

`.env` im Ordner `apps/api/`. Siehe `.env.example`.

- **LLM:** `LLM_BASE_URL` (lokal `http://127.0.0.1:8080`, Docker `http://llm:8080`)
- **Chroma:** `CHROMA_HOST` / `CHROMA_PORT` (Docker: `chroma` / `8000`, lokal: `127.0.0.1` / `8001`)
- **RAG:** `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, `MAX_UPLOAD_MB`; optional `API_KEY` (dann Header `X-API-Key`)

## Abhängigkeiten

```powershell
pip install -r requirements.txt
```

(oder aus Projektroot: `pip install -r apps/api/requirements.txt`)

## So testest du die API (praktisch)

### 1. API starten (Terminal 1)

```bash
cd apps/api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Warte, bis du `Uvicorn running on http://0.0.0.0:8000` siehst.

---

### 2. Test im Browser (am einfachsten)

- **Health:** Im Browser öffnen: **http://127.0.0.1:8000/health**  
  → Du solltest `{"status":"ok"}` sehen.

- **Interaktive Doku:** **http://127.0.0.1:8000/docs**  
  → Swagger UI: Dort kannst du **GET /health** und **POST /api/text/briefing** anklicken, Parameter eintragen und „Execute“ ausführen. Die Antwort siehst du direkt.

---

### 3. Test mit curl (Terminal 2)

**Nur Health (braucht keinen LLM-Server):**

```powershell
curl http://127.0.0.1:8000/health
```

Erwartung: `{"status":"ok"}`

**Briefing (braucht laufenden LLM-Server auf Port 8080):**

```powershell
curl -X POST "http://127.0.0.1:8000/api/text/briefing" -H "Content-Type: application/json" -d "{\"text\":\"Ich habe ein Kapitel über Docker gelesen. Es geht um Images, Container, Volumes und Netzwerke. Erstelle mir ein Smart Briefing.\",\"options\":{\"language\":\"de\",\"tone\":\"neutral\",\"max_keypoints\":10,\"max_headlines\":5}}"
```

---

### 4. Test mit Python-Skript

```bash
cd apps/api
pip install requests
python test_api.py
```

### 5. RAG testen (Ingest + Chat)

```bash
python test_rag.py                  # nur Health-Deps + Chat
python test_rag.py path/to/file.pdf # zusätzlich PDF ingest, dann Chat
```

Oder **PowerShell:** `.\scripts\test-rag.ps1` (Health-Deps, /api/rag/docs, Chat). PDF-Upload am besten über Swagger oder `test_rag.py`.

---

**Kurz:** **/health** und **/health/deps** prüfen. **Briefing** braucht LLM; **RAG** braucht Chroma + Embeddings (beim Start geladen) + optional LLM für Chat. Bei 502: LLM prüfen. Bei 503: Chroma prüfen.
