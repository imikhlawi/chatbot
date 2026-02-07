"""
Praktischer Test der API – ohne Browser.
Vorher: API starten mit  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""
import requests

BASE = "http://127.0.0.1:8000"

def test_health():
    print("1. GET /health ...")
    r = requests.get(f"{BASE}/health")
    r.raise_for_status()
    data = r.json()
    assert data.get("status") == "ok"
    print("   -> OK:", data)
    return True

def test_briefing():
    print("2. POST /api/text/briefing ...")
    payload = {
        "text": "Ich habe ein Kapitel über Docker gelesen. Es geht um Images, Container, Volumes und Netzwerke. Erstelle mir ein Smart Briefing.",
        "options": {
            "language": "de",
            "tone": "neutral",
            "max_keypoints": 10,
            "max_headlines": 5,
        },
    }
    r = requests.post(f"{BASE}/api/text/briefing", json=payload, timeout=320)
    if r.status_code != 200:
        print("   -> Fehler:", r.status_code, r.text[:300])
        return False
    data = r.json()
    print("   -> OK: summary (Anfang):", (data.get("summary") or "")[:150], "...")
    print("   -> keypoints:", len(data.get("keypoints", [])), "Stück")
    return True

if __name__ == "__main__":
    print("API-Test (BASE =", BASE, ")\n")
    try:
        test_health()
        print()
        test_briefing()
        print("\nAlle Tests durchgelaufen.")
    except requests.exceptions.ConnectionError:
        print("Fehler: API nicht erreichbar. Starte zuerst: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print("Fehler:", e)
