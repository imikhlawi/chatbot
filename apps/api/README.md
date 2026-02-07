# PDF-Chatbot API (Schritt 2)

FastAPI-Backend für Smart Briefing. Läuft lokal, ruft einen **lokalen LLM-Server** (z. B. llama.cpp server) per HTTP auf.

## Start

```powershell
cd P:\Chatbot\apps\api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints

- `GET /health` → `{"status":"ok"}`
- `POST /api/text/briefing` → Smart Briefing (JSON, Pydantic-validiert)

## Konfiguration

`.env` im Ordner `apps/api/`. Wichtig: `LLM_BASE_URL` (z. B. `http://127.0.0.1:8080`) und ggf. Port anpassen.

## Abhängigkeiten

```powershell
pip install -r requirements.txt
```

(oder aus Projektroot: `pip install -r apps/api/requirements.txt`)

## So testest du die API (praktisch)

### 1. API starten (Terminal 1)

```powershell
cd P:\Chatbot\apps\api
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

```powershell
cd P:\Chatbot\apps\api
pip install requests
python test_api.py
```

Das Skript testet zuerst `/health`, dann `/api/text/briefing`. Wenn die API nicht läuft: Hinweis „API nicht erreichbar“. Wenn der LLM-Server nicht läuft: Briefing-Teil schlägt mit 502 fehl.

---

**Kurz:** Zuerst **/health** prüfen (beweist, dass die API läuft). **/api/text/briefing** funktioniert nur, wenn zusätzlich der LLM-Server (z. B. llama.cpp) unter der in `.env` eingetragenen URL läuft. Bei 502: LLM-Server starten bzw. `LLM_BASE_URL` und Endpoint prüfen.
