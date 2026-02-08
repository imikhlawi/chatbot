"use client";

import { useState } from "react";
import { ingestPdf, type IngestResponse } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [res, setRes] = useState<IngestResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onUpload() {
    if (!file) return;
    setLoading(true);
    setErr(null);
    setRes(null);
    try {
      const r = await ingestPdf(file);
      setRes(r);
      localStorage.setItem("last_doc_id", r.doc_id);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>Upload & Index</h1>
      <p style={{ marginTop: 8, maxWidth: 800 }}>
        PDF hochladen → API indexiert in Chroma → du bekommst doc_id zurück.
      </p>

      <div style={{ marginTop: 16 }}>
        <input
          type="file"
          accept="application/pdf,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button
          onClick={onUpload}
          disabled={!file || loading}
          style={{
            marginLeft: 12,
            padding: "10px 16px",
            borderRadius: 10,
            border: "1px solid #444",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Indexiere..." : "Upload & Ingest"}
        </button>
      </div>

      {res && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontWeight: 700 }}>Ergebnis</h3>
          <pre
            style={{
              background: "#111",
              color: "#eee",
              padding: 16,
              borderRadius: 12,
              overflowX: "auto",
            }}
          >
            {JSON.stringify(res, null, 2)}
          </pre>

          {res.status === "skipped" && (
            <div style={{ marginTop: 10, color: "#ffcc00" }}>
              <b>Hinweis:</b> Scan-PDF erkannt. OCR ist noch nicht integriert.
            </div>
          )}
        </div>
      )}

      {err && (
        <div style={{ marginTop: 16, color: "#ff6b6b" }}>
          <b>Fehler:</b> {err}
          <div style={{ marginTop: 6, color: "#bbb" }}>
            Typisch: 413 (zu groß), 400 (kein PDF), 503 (Chroma down), 500
            (Embeddings).
          </div>
          {(err.includes("fetch") || err.includes("Network")) && (
            <div style={{ marginTop: 10, padding: 10, background: "#1a1a1a", borderRadius: 8, fontSize: 12 }}>
              <b style={{ color: "#ffcc00" }}>Bei NetworkError prüfen:</b>
              <ul style={{ marginTop: 6, paddingLeft: 18 }}>
                <li>API läuft? Im Browser: <a href={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/health/deps`} target="_blank" rel="noopener noreferrer" style={{ color: "#7dd3fc" }}>/health/deps</a> öffnen</li>
                <li>In <code>apps/api/.env</code>: <code>CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000</code> → API neu starten</li>
                <li>In <code>apps/ui/.env.local</code>: <code>NEXT_PUBLIC_API_BASE_URL=http://localhost:8000</code> (kein <code>api:8000</code> im Browser)</li>
              </ul>
            </div>
          )}
        </div>
      )}

      <div style={{ marginTop: 22, color: "#bbb" }}>
        <p>
          Nächster Schritt: <a href="/chat">/chat</a> öffnen und mit dem
          gespeicherten <code>doc_id</code> chatten.
        </p>
        <p style={{ marginTop: 8 }}>
          <a href="/">Home</a> · <a href="/chat">Chat</a>
        </p>
      </div>
    </main>
  );
}
