# PDF-Chatbot (RAG + lokales LLM)

**Erste Version** – Ein Chatbot, der Fragen zu deinen PDF-Dokumenten beantwortet (RAG) und bei allgemeinen Fragen frei antwortet. Läuft vollständig lokal (Embeddings, Vector-Store, LLM). Weitere Features sind geplant.

---

## Was es kann

- **Fragen zu deinen PDFs:** Sucht relevante Abschnitte und antwortet nur auf Basis dieses Kontexts. Zeigt die gefundenen Stellen und eine KI-Zusammenfassung.
- **Allgemeine Fragen:** Wenn die Eingabe nicht zu den PDF-Inhalten passt, antwortet die KI frei (z. B. Code, Erklärungen). Ausgabe wird gestreamt.
- **Lokal:** Kein Cloud-API, kein API-Key. Genutzt werden: LangChain, FAISS, sentence-transformers, ein GGUF-Modell über llama-cpp-python.

---

## Voraussetzungen

- Python 3.8 (damit getestet)
- Genug RAM (z. B. 32B-Modell: grob 20 GB+; 7B deutlich weniger)
- Platz für Modell und Abhängigkeiten (mehrere GB)

---

## Projektstruktur

```
Chatbot/
├── data/                 → PDF-Dateien hier ablegen (nicht im Repo)
├── llm_model/            → GGUF-Modell hier ablegen (nicht im Repo)
├── faiss_index/         → Wird beim ersten Lauf erzeugt (lokal)
├── pdf_chatbot.ipynb     → Hauptnotebook
├── requirements.txt
└── README.md
```

`data/` und `llm_model/` enthalten im Repo nur kurze READMEs; PDFs und Modell-Dateien liegen bei dir und werden nicht hochgeladen.

---

## Einrichtung

### 1. Virtuelle Umgebung (empfohlen)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
```

### 2. Abhängigkeiten

```bash
pip install -r requirements.txt
```

Für **GPU** (CUDA) mit llama-cpp-python vor dem Install z. B.:

```bash
set CMAKE_ARGS=-DGGML_CUDA=on
pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 3. NLTK (optional vorab)

Wird im Notebook bei Bedarf nachgeladen. Ohne Internet vorher:

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 4. Modell

- GGUF-Modell z. B. von [Qwen2.5-Coder-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct-GGUF) (oder 7B-Variante) herunterladen.
- `.gguf`-Datei in `llm_model/` legen.
- Im Notebook in der Zelle „Lokales LLM laden“ den Pfad anpassen, falls der Dateiname abweicht (Standard: `llm_model/qwen2.5-coder-32b-instruct-q4_k_m.gguf`).

### 5. PDFs

- PDF-Dateien in `data/` legen.
- Das Notebook lädt alle `*.pdf` aus `data/` und baut daraus den FAISS-Index.

---

## Nutzung

1. Jupyter starten und `pdf_chatbot.ipynb` öffnen.

2. Zellen **der Reihe nach** ausführen:
   - Imports & NLTK
   - Konfiguration (`FAISS_INDEX_PATH`)
   - PDF laden (`load_pdf("data/")`) und aufteilen (`text_splitter`)
   - Embeddings laden
   - FAISS-Index erzeugen und speichern (beim ersten Mal)
   - LLM laden (LlamaCpp)
   - RAG-Kette (RetrievalQA); lädt bei Bedarf den Index von Disk
   - Falls vorhanden: Chat-Zelle für Fragen

3. **Erster Lauf:** Index-Bau aus den PDFs kann einige Minuten dauern.

4. **Später:** Wenn `faiss_index/` existiert, kann die RAG-Zelle den Index laden, ohne die PDF-Zellen erneut auszuführen.

---

## Ablauf (technisch)

| Schritt | Bedeutung |
|--------|-----------|
| `load_pdf("data/")` | Lädt alle PDFs (PyPDFLoader). |
| `text_splitter(...)` | Chunks (z. B. 1000 Zeichen, 200 Überlappung). |
| HuggingFace-Embeddings | Vektoren für die Chunks (sentence-transformers). |
| FAISS | Vector-Store, schnelle Ähnlichkeitssuche. |
| LlamaCpp | GGUF-Modell für Antworten. |
| RetrievalQA | Sucht Chunks, LLM antwortet nur aus diesem Kontext (RAG). |
| Chat | PDF-Frage → RAG; sonst → freie KI-Antwort (gestreamt). |

---

## Einstellungen im Notebook

- **`FAISS_INDEX_PATH`** – Wo der FAISS-Index liegt (Standard: `./faiss_index`).
- **LLM:** `model_path`, `n_ctx`, `max_tokens`, `temperature`, `repeat_penalty`. Bei wenig RAM/CPU: kleineres Modell oder kleinere `max_tokens`/`n_ctx`.
- **RAG:** `search_kwargs={"k": 2}` – Anzahl Chunks pro Frage. Größeres `k` = mehr Kontext, evtl. langsamer.
- **Chat (falls vorhanden):** `NUR_PDF` (nur PDF-Abschnitte, ohne LLM), `PDF_RELEVANZ_SCHWELLE` (ab wann „allgemeine Frage“).

---

## Nicht ins Repo

- Modelle (`llm_model/*.gguf`, `*.bin`) – zu groß.
- PDFs (`data/*.pdf`) – Datenschutz/Urheberrecht.
- `faiss_index/` – wird lokal aus PDFs erzeugt.
- Caches, `.ipynb_checkpoints/` – in `.gitignore`.

---

## Häufige Probleme

- **Import-Fehler (langchain, …)**  
  `pip install -r requirements.txt` in derselben Umgebung wie Jupyter.

- **„nltk has no attribute 'data'“**  
  Vorher: `nltk.download("punkt")`, `nltk.download("punkt_tab")`.

- **Zu viel RAM / zu langsam**  
  Kleineres Modell (z. B. 7B) oder kleinere `max_tokens`/`n_ctx`.

- **Antworten zu kurz**  
  `max_tokens` in der LLM-Zelle erhöhen.

- **Keine Chat-Zelle**  
  In dieser Version kann das Notebook je nach Stand nur bis zur RAG-Kette gehen; Chat-Logik ggf. manuell ergänzen (Schleife mit `input`, `qa_chain`/`llm`).

---

## Lizenz / Nutzung

Privat und edukativ. Lizenzen der verwendeten Modelle und Daten beachten.

---

## Kurzfassung

```bash
# Im Projektordner:
python -m venv venv
venv\Scripts\activate          # Windows; Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
# GGUF in llm_model/, PDFs in data/
jupyter notebook pdf_chatbot.ipynb
# Zellen nacheinander ausführen.
```

Kein Clone-Link – das Repo enthält nur Code und Anleitung; Modell und PDFs bringst du selbst mit.
