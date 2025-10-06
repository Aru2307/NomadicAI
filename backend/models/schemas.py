from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class AskRequest(BaseModel):
    question: str
    provider: str | None = None  # 'auto' | 'openai' | 'ollama'


class SourceCitation(BaseModel):
    source: str
    page: Optional[int] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    calc: Optional[str] = None


class UploadResponse(BaseModel):
    files_ingested: List[str]
    files_skipped: List[str]
    chunks_added: int
