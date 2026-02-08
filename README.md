# PDF-Chatbot (RAG + lokales LLM)

Chatbot, der Fragen zu deinen PDF-Dokumenten beantwortet (RAG) und mit einem **lokalen LLM** (llama.cpp) antwortet. Läuft vollständig lokal: FastAPI, ChromaDB, sentence-transformers, optionales Jupyter-Notebook.

---

## Was drin ist

| Komponente | Beschreibung |
|------------|--------------|
| **API** (FastAPI) | Health, RAG (Ingest, Chat mit Streaming), Briefing, Docs-Verwaltung |
| **LLM** | llama.cpp Server (Docker), GGUF-Modell |
| **Chroma** | Vector-Store für PDF-Chunks |
| **UI** (Next.js) | Diagnose, Upload, Chat (Echtzeit-Streaming), Docs-Verwaltung |
| **Notebook** | Alternative: Jupyter mit FAISS (ohne Docker) |

---

## Quick Start (Docker + UI)

**Voraussetzung:** Docker (z. B. Docker Desktop), Node.js für die UI.

### 1. Modell ablegen

GGUF-Modell (z. B. [Qwen2.5-Coder-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF)) herunterladen und nach `storage/models/` legen. In `docker-compose.yml` ist derzeit z. B. `qwen2.5-coder-32b-instruct-q4_k_m.gguf` eingetragen – Dateiname anpassen oder Modell entsprechend benennen.

### 2. API + LLM + Chroma starten

Im **Projektroot** (Ordner mit `docker-compose.yml`):

```bash
docker compose up -d --build
```

Nach 1–2 Minuten (Modell lädt): API unter **http://localhost:8000**, Doku unter **http://localhost:8000/docs**.

### 3. Konfiguration API (optional)

```bash
cp apps/api/.env.example apps/api/.env
```

Anpassen nach Bedarf (z. B. `LLM_BASE_URL`, `CHROMA_HOST`, `CORS_ORIGINS`, `API_KEY`). Ohne `.env` nutzt die API die Defaults aus dem Code; Docker setzt `LLM_BASE_URL` und Chroma-Host/Port automatisch.

### 4. UI starten (lokal)

```bash
cd apps/ui
cp .env.example .env.local
npm install
npm run dev
```

Browser: **http://localhost:3000**

- **Home:** „Check deps“ → API/LLM/Chroma-Status
- **Upload:** PDF hochladen → Ingest → `doc_id` für Chat
- **Chat:** Frage stellen → Antwort kommt per Echtzeit-Stream
- **Docs:** Chunks anzeigen, Dokument per `doc_id` löschen

### 5. PDFs

PDFs in `data/` legen (fürs Notebook) oder direkt in der UI unter **Upload** hochladen.

---

## Projektstruktur

```
├── docker-compose.yml      # API, LLM, Chroma
├── apps/
│   ├── api/                # FastAPI (RAG, Briefing, Health)
│   │   ├── .env.example
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   └── ui/                 # Next.js (Upload, Chat, Docs)
│       ├── .env.example
│       ├── package.json
│       └── src/
├── data/                   # PDFs (optional, für Notebook)
├── storage/
│   ├── models/             # GGUF-Modell (nicht im Repo)
│   └── chroma/             # Chroma-Daten (lokal, nicht im Repo)
├── pdf_chatbot.ipynb       # Jupyter-Variante (FAISS)
├── requirements.txt        # Für Notebook
├── START-HIER.md           # Troubleshooting / Start-Checkliste
└── README.md
```

---

## API-Endpoints (Kurz)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/health` | Liveness |
| GET | `/health/deps` | LLM-, Chroma-, Embeddings-Status |
| POST | `/api/rag/ingest` | PDF-Upload → Chroma |
| POST | `/api/rag/chat` | RAG-Chat (vollständige Antwort) |
| POST | `/api/rag/chat/stream` | RAG-Chat (Echtzeit-Stream) |
| GET | `/api/rag/docs` | Collection + Chunk-Anzahl |
| DELETE | `/api/rag/docs/{doc_id}` | Dokument löschen |
| POST | `/api/text/briefing` | Smart Briefing (Freitext) |

Details und Swagger: **http://localhost:8000/docs**

---

## Nicht im Repo (`.gitignore`)

- `storage/models/*.gguf`, `*.bin` – Modell-Dateien
- `storage/chroma/*` – Chroma-Daten
- `data/*.pdf` – PDF-Dateien
- `apps/api/.env`, `apps/ui/.env.local` – lokale Konfiguration
- `venv/`, `node_modules/`, `.next/` – Umgebungen und Builds
- Interne Notizen/Skripte (z. B. `TEST-BEFEHLE.md`, `scripts/`)

---

## Alternative: Jupyter-Notebook

Ohne Docker kannst du nur das Notebook nutzen:

1. `python -m venv venv` und aktivieren
2. `pip install -r requirements.txt`
3. GGUF in `llm_model/` oder `storage/models/`, PDFs in `data/`
4. `jupyter notebook pdf_chatbot.ipynb` – Zellen nacheinander ausführen

Das Notebook nutzt FAISS als Vector-Store und llama-cpp-python direkt (kein separater HTTP-Server).

---

## Lizenz / Nutzung

Privat und edukativ. Lizenzen der verwendeten Modelle und Daten beachten.
