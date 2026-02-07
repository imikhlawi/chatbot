"""
RAG-API testen: /health/deps, optional Ingest (PDF), dann Chat.
Verwendung:
  python test_rag.py
  python test_rag.py path/to/document.pdf
Ohne PDF: nur Health-Deps + Chat (Antwort evtl. "Nicht im Dokument").
Mit PDF: Ingest → Chat mit Frage "Worum geht es in dem Dokument?"
"""
import sys
import requests

BASE = "http://127.0.0.1:8000"
# Optional: wenn API_KEY in .env gesetzt ist
# API_KEY = "your-key"
# HEADERS = {"X-API-Key": API_KEY}
HEADERS = {}


def test_health_deps():
    print("1. GET /health/deps ...")
    r = requests.get(f"{BASE}/health/deps", timeout=5, headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    print("   ", d)
    return d


def test_ingest(pdf_path: str):
    print("2. POST /api/rag/ingest (PDF) ...")
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{BASE}/api/rag/ingest",
            files={"file": (pdf_path, f, "application/pdf")},
            timeout=120,
            headers=HEADERS,
        )
    r.raise_for_status()
    d = r.json()
    print("   doc_id:", d.get("doc_id"), "chunks:", d.get("chunks"), "status:", d.get("status"))
    if d.get("warnings"):
        print("   warnings:", d["warnings"])
    return d.get("doc_id")


def test_chat(question: str, doc_id=None):
    print("3. POST /api/rag/chat ...")
    payload = {"question": question, "doc_id": doc_id}
    r = requests.post(f"{BASE}/api/rag/chat", json=payload, timeout=120, headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    print("   answer (Anfang):", (d.get("answer") or "")[:200], "...")
    print("   citations:", len(d.get("citations", [])), "used_chunks:", d.get("used_chunks"))
    return d


def test_list_docs():
    print("   GET /api/rag/docs ...")
    r = requests.get(f"{BASE}/api/rag/docs", timeout=5, headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    print("   ", d)
    return d


def main():
    pdf_path = (sys.argv[1] if len(sys.argv) > 1 else None) or "test.pdf"
    test_health_deps()
    print()
    doc_id = None
    if pdf_path:
        try:
            doc_id = test_ingest(pdf_path)
            test_list_docs()
        except FileNotFoundError:
            print("   (Keine Datei", pdf_path, "– Ingest übersprungen)")
        except Exception as e:
            print("   Ingest fehlgeschlagen:", e)
    print()
    test_chat("Worum geht es in dem Dokument?" if doc_id else "Was steht in den Dokumenten?", doc_id=doc_id)
    print("\nRAG-Tests durchgelaufen.")


if __name__ == "__main__":
    main()
