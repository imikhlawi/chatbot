# PDF-Chatbot UI

Next.js-UI für Diagnose, PDF-Upload, RAG-Chat (Echtzeit-Streaming) und Docs-Verwaltung.

## Voraussetzung

Die API muss laufen (z. B. `docker compose up -d` im Projektroot).

## Setup

```bash
cd apps/ui
cp .env.example .env.local
npm install
```

In `.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`. Optional: `NEXT_PUBLIC_API_KEY`, falls die API einen API-Key verlangt.

## Start

```bash
npm run dev
```

Browser: **http://localhost:3000**

- **/** – Check deps (API/LLM/Chroma)
- **/upload** – PDF hochladen, Ingest
- **/chat** – RAG-Chat mit Echtzeit-Streaming
- **/docs** – Chunks anzeigen, Dokument löschen

## Build (Produktion)

```bash
npm run build
npm start
```
