# PDF-Chatbot – Start (Schritt für Schritt)

Wenn **nichts funktioniert**, genau in dieser Reihenfolge prüfen.

---

## 1. API (Docker)

Im Projektroot (dort wo `docker-compose.yml` liegt):

```bash
docker compose up -d --build
```

Warten, bis alle Container laufen (ca. 30–60 Sekunden, API lädt Embeddings):

```bash
docker compose ps
```

Alle drei: **api**, **chroma**, **llm** sollten **Up** sein.

**Falls die API abstürzt:**

```bash
docker logs chatbot-api --tail 80
```

Häufig: Embedding-Modell lädt beim ersten Start lange oder Speicher reicht nicht.

---

## 2. API im Browser testen

Im **Browser** (Chrome/Edge/Firefox) öffnen:

**http://localhost:8000/health/deps**

- Du solltest **JSON** sehen (z. B. `status`, `llm`, `chroma`, `embeddings`, `collection`).
- Wenn die Seite **nicht lädt** (Verbindung abgelehnt / Zeitüberschreitung):
  - API läuft nicht → `docker compose ps` und `docker logs chatbot-api --tail 50`.

---

## 3. UI (lokal, ohne Docker)

**Zwei Terminals:**

**Terminal 1 – API läuft schon (Docker, siehe oben).**

**Terminal 2 – UI starten:**

```bash
cd apps/ui
npm install
npm run dev
```

Im Browser öffnen: **http://localhost:3000** (oder http://127.0.0.1:3000).

- Auf der Startseite **„Check deps“** klicken.
- Erwartung: Es erscheint JSON und die Badges (LLM, Chroma, …).

**Wenn hier „NetworkError“ oder „fetch failed“ kommt:**

| Prüfung | Aktion |
|--------|--------|
| API erreichbar? | Im Browser **http://localhost:8000/health/deps** öffnen. Wenn das nicht geht, API starten (Schritt 1). |
| CORS | In `apps/api/.env` muss stehen: `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` (oder du lässt die Zeile weg – dann gilt der Standard). Danach: `docker compose restart api`. |
| Richtige URL | In `apps/ui/.env.local`: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` (ohne Slash am Ende). **Nicht** `http://api:8000` (gilt nur im Docker-Netz). Nach Änderung: UI mit Strg+F5 neu laden. |
| API-Key | Wenn in `apps/api/.env` ein `API_KEY=...` gesetzt ist, in `apps/ui/.env.local` eintragen: `NEXT_PUBLIC_API_KEY=derselbe_wert`. Sonst bekommst du 401. |

---

## 4. Upload testen

- Unter **http://localhost:3000/upload** eine **kleine Text-PDF** (kein reiner Scan) auswählen.
- **„Upload & Ingest“** klicken.
- Erwartung: JSON mit `doc_id`, `chunks`, `status: "indexed"`.

**Wenn wieder NetworkError:** Siehe Abschnitt 3 (CORS, URL, API-Key).

**Wenn 413:** PDF zu groß → in `apps/api/.env` z. B. `MAX_UPLOAD_MB=50` prüfen oder kleinere PDF nehmen.

**Wenn 503:** Chroma nicht erreichbar → `docker compose ps` und `docker logs chatbot-chroma --tail 30`.

---

## 5. Chat testen

- Nach erfolgreichem Upload: **http://localhost:3000/chat** öffnen.
- `doc_id` sollte schon eingetragen sein (kommt aus dem Upload).
- Eine Frage eingeben, die im PDF vorkommt → **„Frage senden“**.
- Erwartung: Antwort + Quellen (Citations).

**Wenn 502 / „LLM nicht erreichbar“:**

- **LLM lädt noch:** Das Modell (z. B. 32B) kann 1–2 Minuten brauchen. Einfach etwas warten und erneut „Frage senden“ klicken.
- **LLM-URL in Docker:** Die API muss im Container den LLM unter `http://llm:8080` erreichen. In `docker-compose.yml` ist dafür `LLM_BASE_URL=http://llm:8080` gesetzt. Nach Änderung: `docker compose up -d` (oder `docker compose restart api`).
- **Logs prüfen:** `docker logs chatbot-llm --tail 50` – wenn dort „listening on 0.0.0.0:8080“ o. ä. steht, ist der LLM bereit.

---

## Kurz-Checkliste

- [ ] `docker compose up -d` im Projektroot (Ordner mit `docker-compose.yml`)
- [ ] Im Browser **http://localhost:8000/health/deps** zeigt JSON
- [ ] `apps/api/.env` enthält `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` (oder Zeile fehlt → Standard)
- [ ] `apps/ui/.env.local` enthält `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- [ ] Wenn API_KEY gesetzt: `NEXT_PUBLIC_API_KEY` in der UI gesetzt
- [ ] UI mit `npm run dev` in `apps/ui` gestartet, Browser: **http://localhost:3000**
- [ ] Nach Änderungen an .env: API neu starten (`docker compose restart api`), UI ggf. Hard-Reload (Strg+F5)
