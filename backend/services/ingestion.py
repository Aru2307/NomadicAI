from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PDFMinerLoader,
    TextLoader,
    UnstructuredFileLoader,
)


SUPPORTED_EXT = {".pdf", ".txt", ".docx", ".doc"}


def _loader_for_path(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return PDFMinerLoader(str(path))
    if suffix == ".txt":
        return TextLoader(str(path), encoding="utf-8")
    # Attempt generic unstructured for office docs and others
    return UnstructuredFileLoader(str(path))


def load_file_as_documents(path: Path) -> List[Document]:
    """Load file and split into chunks with useful metadata.

    Returns empty list if file type unsupported or parsing fails.
    """
    if not path.exists() or not path.is_file():
        return []

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXT:
        # Best-effort parse with unstructured (may fail quietly)
        loader = UnstructuredFileLoader(str(path))
    else:
        loader = _loader_for_path(path)

    try:
        raw_docs = loader.load()
    except Exception:
        return []

    # Ensure metadata includes source
    for d in raw_docs:
        d.metadata = d.metadata or {}
        d.metadata.setdefault("source", path.name)
        d.metadata.setdefault("file_path", str(path))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    docs = splitter.split_documents(raw_docs)

    # Keep short chunks by filtering tiny fragments
    docs = [d for d in docs if d.page_content and len(d.page_content.strip()) > 50]
    return docs
