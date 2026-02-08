"use client";

import { useState } from "react";
import { healthDeps, type HealthDeps } from "@/lib/api";

export default function Home() {
  const [data, setData] = useState<HealthDeps | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onCheck() {
    setLoading(true);
    setErr(null);
    try {
      const d = await healthDeps();
      setData(d);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  const llmOk = data?.llm?.status === "ok";
  const chromaOk = data?.chroma?.status === "ok";

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 24, fontWeight: 700 }}>PDF-Chatbot UI</h1>
      <p style={{ marginTop: 8, maxWidth: 800 }}>
        Diese Seite prüft, ob API / LLM / Chroma erreichbar sind. Wenn hier
        alles grün ist, funktionieren Upload und Chat später stabil.
      </p>

      <button
        onClick={onCheck}
        disabled={loading}
        style={{
          marginTop: 16,
          padding: "10px 16px",
          borderRadius: 10,
          border: "1px solid #444",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Prüfe..." : "Check deps"}
      </button>

      {data && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: "flex", gap: 12, marginBottom: 12, flexWrap: "wrap" }}>
            <Badge ok={llmOk} label={`LLM: ${data.llm.status}`} />
            <Badge ok={chromaOk} label={`Chroma: ${data.chroma.status}`} />
            <Badge ok={true} label={`Embeddings: ${data.embeddings.status}`} />
            <Badge ok={true} label={`Collection: ${data.collection}`} />
          </div>

          <pre
            style={{
              background: "#111",
              color: "#eee",
              padding: 16,
              borderRadius: 12,
              overflowX: "auto",
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}

      {err && (
        <div style={{ marginTop: 16, color: "#ff6b6b" }}>
          <b>Fehler:</b> {err}
          <div style={{ marginTop: 6, color: "#bbb" }}>
            Häufig: CORS, falsche API URL, API nicht gestartet.
          </div>
        </div>
      )}

      <div style={{ marginTop: 22, color: "#bbb" }}>
        <p>
          <b>Nächste Schritte:</b> <a href="/upload">Upload</a> → <a href="/chat">Chat</a> · <a href="/docs">Docs</a>
        </p>
      </div>
    </main>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      style={{
        padding: "6px 10px",
        borderRadius: 999,
        border: "1px solid",
        borderColor: ok ? "#2ecc71" : "#e74c3c",
        color: ok ? "#2ecc71" : "#e74c3c",
        fontSize: 12,
      }}
    >
      {label}
    </span>
  );
}
