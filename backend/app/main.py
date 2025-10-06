from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.services.rag import RAGPipeline, get_default_embeddings, get_default_llm
from backend.services.ingestion import load_file_as_documents
from backend.models.schemas import AskRequest, AskResponse, HealthResponse, UploadResponse


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="AI Copilot for Engineers - Backend", version="0.1.0")

# Allow local dev from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize core components
embeddings = get_default_embeddings()
llm = get_default_llm()
rag = RAGPipeline(
    persist_directory=str(CHROMA_DIR),
    embeddings=embeddings,
    llm=llm,
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    total_chunks = 0
    accepted_files: List[str] = []
    skipped_files: List[str] = []

    for uf in files:
        dest_path = UPLOADS_DIR / uf.filename
        try:
            with dest_path.open("wb") as f:
                f.write(await uf.read())
        except Exception as exc:
            skipped_files.append(uf.filename)
            continue

        try:
            docs = load_file_as_documents(dest_path)
            if not docs:
                skipped_files.append(uf.filename)
                continue

            added = rag.add_documents(docs)
            total_chunks += added
            accepted_files.append(uf.filename)
        except Exception as exc:
            skipped_files.append(uf.filename)

    return UploadResponse(
        files_ingested=accepted_files,
        files_skipped=skipped_files,
        chunks_added=total_chunks,
    )


@app.post("/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest) -> AskResponse:
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty")

    provider = None if payload.provider in (None, "", "auto") else payload.provider
    answer, sources, calc = rag.answer(payload.question, provider=provider)
    return AskResponse(answer=answer, sources=sources, calc=calc)
