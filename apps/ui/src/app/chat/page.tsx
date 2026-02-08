"use client";

import { useEffect, useState } from "react";
import { ragChatStream, type Citation } from "@/lib/api";

export default function ChatPage() {
  const [docId, setDocId] = useState<string>("");
  const [q, setQ] = useState<string>("");
  const [streamingAnswer, setStreamingAnswer] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [usedChunks, setUsedChunks] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const last = localStorage.getItem("last_doc_id");
    if (last) setDocId(last);
  }, []);

  async function onAsk() {
    if (!q.trim()) return;
    setLoading(true);
    setErr(null);
    setStreamingAnswer("");
    setCitations([]);
    setUsedChunks(0);
    try {
      for await (const event of ragChatStream(q, docId.trim() || undefined)) {
        if (event.type === "meta") {
          setCitations(event.citations);
          setUsedChunks(event.used_chunks);
        } else if (event.type === "token") {
          setStreamingAnswer((prev) => prev + event.content);
        } else if (event.type === "error") {
          setErr(event.detail);
          break;
        }
        // "done" → einfach weitermachen, loading unten auf false
      }
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  const hasAnswer = streamingAnswer.length > 0 || citations.length > 0;

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>RAG Chat</h1>
      <p style={{ marginTop: 8, maxWidth: 900 }}>
        Stelle Fragen zum indexierten PDF. Die Antwort kommt vom lokalen LLM,
        basiert aber auf Chroma-Retrieval. <b>Echtzeit-Streaming:</b> Du siehst
        die Antwort, während sie erzeugt wird.
      </p>

      <div style={{ marginTop: 16 }}>
        <label style={{ display: "block", fontSize: 13, color: "#bbb" }}>
          doc_id (optional)
        </label>
        <input
          value={docId}
          onChange={(e) => setDocId(e.target.value)}
          placeholder="leer = ohne Filter, empfohlen: doc_id setzen"
          style={{
            width: "100%",
            maxWidth: 500,
            padding: 10,
            borderRadius: 10,
            border: "1px solid #444",
            background: "#111",
            color: "#fff",
            marginTop: 6,
          }}
        />
      </div>

      <div style={{ marginTop: 16 }}>
        <label style={{ display: "block", fontSize: 13, color: "#bbb" }}>
          Frage
        </label>
        <textarea
          value={q}
          onChange={(e) => setQ(e.target.value)}
          rows={4}
          placeholder="z. B.: Erkläre Kapitel 2 in 5 Stichpunkten."
          style={{
            width: "100%",
            maxWidth: 500,
            padding: 10,
            borderRadius: 10,
            border: "1px solid #444",
            background: "#111",
            color: "#fff",
            marginTop: 6,
          }}
        />
        <button
          onClick={onAsk}
          disabled={loading}
          style={{
            marginTop: 10,
            padding: "10px 16px",
            borderRadius: 10,
            border: "1px solid #444",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Streamt..." : "Frage senden"}
        </button>
      </div>

      {hasAnswer && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontWeight: 700 }}>
            Antwort {loading && <span style={{ color: "#888" }}>(läuft…)</span>}
          </h3>
          <div
            style={{
              background: "#111",
              color: "#eee",
              padding: 16,
              borderRadius: 12,
              maxWidth: 700,
              minHeight: 60,
            }}
          >
            <div style={{ whiteSpace: "pre-wrap" }}>
              {streamingAnswer || (loading ? "…" : "")}
            </div>
          </div>

          <h3 style={{ fontWeight: 700, marginTop: 14 }}>Quellen (Citations)</h3>
          {citations.length > 0 ? (
            <div style={{ display: "grid", gap: 10, maxWidth: 700 }}>
              {citations.map((c, i) => (
                <div
                  key={i}
                  style={{
                    background: "#111",
                    color: "#eee",
                    padding: 14,
                    borderRadius: 12,
                  }}
                >
                  <div style={{ fontSize: 12, color: "#bbb" }}>
                    <b>{c.filename}</b> — Seite {c.page ?? "?"} — Score {c.score}
                  </div>
                  <div
                    style={{ marginTop: 6, fontSize: 13, whiteSpace: "pre-wrap" }}
                  >
                    {c.excerpt}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: "#bbb" }}>
              {loading
                ? "Quellen werden geladen…"
                : "Keine Quellen gefunden (Frage evtl. nicht im Dokument)."}
            </div>
          )}
        </div>
      )}

      {err && (
        <div style={{ marginTop: 16, color: "#ff6b6b" }}>
          <b>Fehler:</b> {err}
          <div style={{ marginTop: 6, color: "#bbb" }}>
            Typisch: 502 (LLM down), 503 (Chroma down), 404 (doc_id nicht
            gefunden), 500 (Prompt/Parsing).
          </div>
        </div>
      )}

      <div style={{ marginTop: 22, color: "#bbb" }}>
        <p>
          <a href="/">Home</a> · <a href="/upload">Upload</a>
        </p>
      </div>
    </main>
  );
}
