"use client";

import { useEffect, useState } from "react";
import { ragDocs, deleteDoc, type DocsInfo } from "@/lib/api";

export default function DocsPage() {
  const [info, setInfo] = useState<DocsInfo | null>(null);
  const [docId, setDocId] = useState("");
  const [lastDoc, setLastDoc] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(false);
  const [loadingDel, setLoadingDel] = useState(false);

  async function loadInfo() {
    setLoadingInfo(true);
    setErr(null);
    try {
      const d = await ragDocs();
      setInfo(d);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Failed to load docs info");
    } finally {
      setLoadingInfo(false);
    }
  }

  useEffect(() => {
    const last = localStorage.getItem("last_doc_id") || "";
    setLastDoc(last);
    setDocId(last);
    loadInfo();
  }, []);

  async function onDelete(id: string) {
    if (!id.trim()) return;
    setLoadingDel(true);
    setErr(null);
    setMsg(null);
    try {
      const r = await deleteDoc(id.trim());
      setMsg(`Deleted doc_id=${id} (${JSON.stringify(r)})`);
      if (id.trim() === (localStorage.getItem("last_doc_id") || "")) {
        localStorage.removeItem("last_doc_id");
        setLastDoc("");
      }
      await loadInfo();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setLoadingDel(false);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700 }}>Docs / Storage</h1>
      <p style={{ marginTop: 8, maxWidth: 900, color: "#bbb" }}>
        Verwaltung der Chroma-Collection: count ansehen, Dokumente löschen.
      </p>

      <div style={{ marginTop: 14 }}>
        <button
          onClick={loadInfo}
          disabled={loadingInfo}
          style={{
            padding: "10px 16px",
            borderRadius: 10,
            border: "1px solid #444",
          }}
        >
          {loadingInfo ? "Lade..." : "Refresh"}
        </button>
      </div>

      {info && (
        <div style={{ marginTop: 16 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Badge label={`Collection: ${info.collection}`} />
            <Badge label={`Chunks: ${info.total_chunks}`} />
          </div>
        </div>
      )}

      <div style={{ marginTop: 18 }}>
        <h3 style={{ fontWeight: 700 }}>Delete by doc_id</h3>
        <div style={{ marginTop: 8 }}>
          <input
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="doc_id"
            style={{
              width: "100%",
              maxWidth: 400,
              padding: 10,
              borderRadius: 10,
              border: "1px solid #444",
              background: "#111",
              color: "#fff",
            }}
          />
          <div
            style={{
              marginTop: 10,
              display: "flex",
              gap: 10,
              flexWrap: "wrap",
            }}
          >
            <button
              onClick={() => onDelete(docId)}
              disabled={loadingDel}
              style={{
                padding: "10px 16px",
                borderRadius: 10,
                border: "1px solid #444",
              }}
            >
              {loadingDel ? "Deleting..." : "Delete doc_id"}
            </button>
            <button
              onClick={() => lastDoc && onDelete(lastDoc)}
              disabled={!lastDoc || loadingDel}
              style={{
                padding: "10px 16px",
                borderRadius: 10,
                border: "1px solid #444",
              }}
            >
              Delete last_doc_id
            </button>
          </div>
          {lastDoc && (
            <div style={{ marginTop: 8, color: "#bbb", fontSize: 13 }}>
              last_doc_id: <code>{lastDoc}</code>
            </div>
          )}
        </div>
      </div>

      {msg && (
        <div style={{ marginTop: 16, color: "#2ecc71" }}>{msg}</div>
      )}
      {err && (
        <div style={{ marginTop: 16, color: "#ff6b6b" }}>
          <b>Fehler:</b> {err}
        </div>
      )}

      <div style={{ marginTop: 22, color: "#bbb" }}>
        <a href="/" style={{ marginRight: 12 }}>
          Home
        </a>
        <a href="/upload" style={{ marginRight: 12 }}>
          Upload
        </a>
        <a href="/chat">Chat</a>
      </div>
    </main>
  );
}

function Badge({ label }: { label: string }) {
  return (
    <span
      style={{
        padding: "6px 10px",
        borderRadius: 999,
        border: "1px solid #666",
        color: "#ddd",
        fontSize: 12,
      }}
    >
      {label}
    </span>
  );
}
