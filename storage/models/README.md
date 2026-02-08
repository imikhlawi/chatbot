# GGUF-Modelle

Hier das **LLM-Modell** ablegen (z. B. für Docker).

**Dateiname:** In `docker-compose.yml` ist derzeit z. B. `qwen2.5-coder-32b-instruct-q4_k_m.gguf` eingetragen. Modell entsprechend benennen oder `docker-compose.yml` anpassen.

**Beispiel (Projektroot):**

```bash
# Linux/macOS
cp /pfad/zu/qwen2.5-coder-32b-instruct-q4_k_m.gguf storage/models/

# Windows (PowerShell)
copy C:\Pfad\zu\qwen2.5-coder-32b-instruct-q4_k_m.gguf storage\models\
```

**Nicht in Git pushen** – in `.gitignore` ausgeschlossen.
