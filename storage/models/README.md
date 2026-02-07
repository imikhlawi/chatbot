# GGUF-Modelle

Hier das Modell ablegen, z. B.:

`qwen2.5-coder-32b-instruct-q4_k_m.gguf`

Kopieren z. B. aus `llm_model/` in diesen Ordner (aus dem Projektroot):

```bash
# Windows (PowerShell)
copy llm_model\qwen2.5-coder-32b-instruct-q4_k_m.gguf storage\models\

# Linux/macOS
cp llm_model/qwen2.5-coder-32b-instruct-q4_k_m.gguf storage/models/
```

Nicht in Git pushen (in `.gitignore`).
