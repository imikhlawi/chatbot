"""Pydantic-Schemas für RAG: Ingest, Chat, Citations."""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    bytes: int
    pages: int
    chunks: int
    collection: str
    status: Literal["indexed", "skipped"]
    warnings: List[str] = Field(default_factory=list)
    elapsed_ms: int


class Citation(BaseModel):
    chunk_id: str
    filename: str
    page: Optional[int] = None
    score: float
    excerpt: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, description="Frage an die dokumentierte Wissensbasis")
    doc_id: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    mode: Literal["docs_only", "hybrid"] = "docs_only"
    language: Literal["de", "en"] = "de"
    return_context: bool = False


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    used_chunks: int = 0
    doc_id: Optional[str] = None
    collection: str
    context_preview: Optional[str] = None  # nur wenn return_context=True
