/**
 * API-Client für PDF-Chatbot-Backend.
 * Basis-URL und optionaler API-Key aus .env.local (NEXT_PUBLIC_*).
 */

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const apiKey = process.env.NEXT_PUBLIC_API_KEY;

function headers(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...(extra || {}) };
  if (apiKey) h["X-API-Key"] = apiKey;
  return h;
}

async function handle<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: unknown = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    /* ignore */
  }
  if (!res.ok) {
    const detail =
      (data as { detail?: string })?.detail ?? text ?? `HTTP ${res.status}`;
    throw new Error(String(detail));
  }
  return data as T;
}

// --- Etappe 1: Health / Deps ---

export type HealthDeps = {
  status: string;
  llm: { status: string; code?: number; error?: string };
  chroma: { status: string; code?: number; error?: string };
  embeddings: { status: string };
  collection: string;
};

export async function healthDeps(): Promise<HealthDeps> {
  const res = await fetch(`${baseUrl}/health/deps`, {
    method: "GET",
    headers: headers(),
    cache: "no-store",
  });
  return handle<HealthDeps>(res);
}

// --- Etappe 2: Ingest ---

export type IngestResponse = {
  doc_id: string;
  filename: string;
  bytes: number;
  pages: number;
  chunks: number;
  collection: string;
  status: "indexed" | "skipped";
  warnings: string[];
  elapsed_ms: number;
};

const INGEST_TIMEOUT_MS = 120_000; // 2 Min – Embedding + Chroma können lange dauern

export async function ingestPdf(file: File): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), INGEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${baseUrl}/api/rag/ingest`, {
      method: "POST",
      headers: headers(),
      body: form,
      signal: controller.signal,
    });
    return handle<IngestResponse>(res);
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("Upload-Timeout (Server braucht zu lange). PDF evtl. verkleinern.");
    }
    throw e;
  } finally {
    clearTimeout(timeoutId);
  }
}

// --- Etappe 3: RAG Chat ---

export type Citation = {
  chunk_id: string;
  filename: string;
  page?: number | null;
  score: number;
  excerpt: string;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  used_chunks: number;
  doc_id?: string | null;
  collection: string;
};

// --- Docs (Collection + Delete) ---

export type DocsInfo = {
  collection: string;
  total_chunks: number;
};

export async function ragDocs(): Promise<DocsInfo> {
  const res = await fetch(`${baseUrl}/api/rag/docs`, {
    method: "GET",
    headers: headers(),
    cache: "no-store",
  });
  return handle<DocsInfo>(res);
}

export async function deleteDoc(
  docId: string
): Promise<{ status: string; doc_id: string }> {
  const res = await fetch(
    `${baseUrl}/api/rag/docs/${encodeURIComponent(docId)}`,
    {
      method: "DELETE",
      headers: headers(),
    }
  );
  return handle<{ status: string; doc_id: string }>(res);
}

export async function ragChat(
  question: string,
  docId?: string
): Promise<ChatResponse> {
  const body: { question: string; doc_id?: string } = { question };
  if (docId) body.doc_id = docId;

  const res = await fetch(`${baseUrl}/api/rag/chat`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  return handle<ChatResponse>(res);
}

// --- RAG Chat Stream (Echtzeit) ---

export type StreamMeta = {
  type: "meta";
  citations: Citation[];
  used_chunks: number;
  doc_id?: string | null;
  collection: string;
};

export type StreamToken = { type: "token"; content: string };
export type StreamDone = { type: "done" };
export type StreamError = { type: "error"; detail: string };

export type StreamEvent = StreamMeta | StreamToken | StreamDone | StreamError;

/** RAG-Chat als Stream: liefert nacheinander meta, token, token, …, done (oder error). */
export async function* ragChatStream(
  question: string,
  docId?: string
): AsyncGenerator<StreamEvent> {
  const body: { question: string; doc_id?: string } = { question };
  if (docId) body.doc_id = docId;

  const res = await fetch(`${baseUrl}/api/rag/chat/stream`, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    let detail: string;
    try {
      const d = JSON.parse(text);
      detail = d.detail ?? text;
    } catch {
      detail = text || `HTTP ${res.status}`;
    }
    yield { type: "error", detail };
    return;
  }
  const reader = res.body?.getReader();
  if (!reader) {
    yield { type: "error", detail: "Kein Response-Body" };
    return;
  }
  const dec = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += dec.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          const event = JSON.parse(trimmed) as StreamEvent;
          yield event;
          if (event.type === "error" || event.type === "done") return;
        } catch {
          /* ignore malformed line */
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
