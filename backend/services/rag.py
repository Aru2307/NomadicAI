from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import Chroma

# Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# LLMs
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

from backend.models.schemas import SourceCitation
from backend.services.calcs import try_compute


@dataclass
class RAGConfig:
    persist_directory: str
    search_k: int = 4


def get_default_embeddings():
    """Choose embeddings: OpenAI if key present else local HF."""
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model="text-embedding-3-small")
    # Local default
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def get_default_llm():
    """Choose LLM: OpenAI if key present else Ollama (llama3.1).

    For Ollama, allow configuring the base URL via OLLAMA_BASE_URL (default http://ollama:11434).
    """
    if os.getenv("OPENAI_API_KEY"):
        # Fast, inexpensive default model
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    # Local model via Ollama server (ensure `ollama serve` is running)
    model_name = os.getenv("OLLAMA_MODEL", "llama3.1")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    return ChatOllama(model=model_name, temperature=0.0, base_url=base_url)


class RAGPipeline:
    def __init__(self, persist_directory: str, embeddings, llm, search_k: int = 4):
        self.persist_directory = persist_directory
        self.embeddings = embeddings
        self.llm = llm
        self.search_k = search_k

        self.vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )
        self.retriever = self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": self.search_k}
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an engineering AI. Answer succinctly and professionally.\n"
                    "Use the provided context to ground your answer.\n"
                    "If you are unsure or the context lacks details, say so.\n"
                    "Cite sources by filename (and page if available) using markdown bullets under 'Sources'.\n",
                ),
                (
                    "human",
                    "Question: {question}\n\n"
                    "Context:\n{context}\n\n"
                    "Produce a concise answer first, then a 'Sources' section with citations.",
                ),
            ]
        )

    def add_documents(self, docs: List[Document]) -> int:
        if not docs:
            return 0
        self.vectorstore.add_documents(docs)
        self.vectorstore.persist()
        return len(docs)

    @staticmethod
    def _format_docs_for_context(docs: List[Document]) -> Tuple[str, List[SourceCitation]]:
        lines: List[str] = []
        citations: List[SourceCitation] = []
        for idx, d in enumerate(docs, start=1):
            source = d.metadata.get("source") or d.metadata.get("file_path") or "unknown"
            page = d.metadata.get("page")
            snippet = d.page_content.strip().replace("\n", " ")
            snippet = snippet[:800]
            lines.append(f"[{idx}] Source: {source} | Page: {page if page is not None else '-'}\n{snippet}")
            citations.append(SourceCitation(source=source, page=page))
        context = "\n\n".join(lines)
        # Deduplicate citations while preserving order
        seen = set()
        unique_citations: List[SourceCitation] = []
        for c in citations:
            key = (c.source, c.page)
            if key in seen:
                continue
            seen.add(key)
            unique_citations.append(c)
        return context, unique_citations

    def answer(self, question: str, provider: Optional[str] = None) -> Tuple[str, List[SourceCitation], Optional[str]]:
        # Retrieval
        docs = self.retriever.get_relevant_documents(question)
        context, citations = self._format_docs_for_context(docs)

        # LLM answer
        messages = self.prompt.format_messages(question=question, context=context)
        # Allow per-request provider override
        llm_to_use = self.llm
        if provider is not None and provider.lower() in {"openai", "ollama"}:
            if provider.lower() == "openai" and os.getenv("OPENAI_API_KEY"):
                llm_to_use = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
            elif provider.lower() == "ollama":
                model_name = os.getenv("OLLAMA_MODEL", "llama3.1")
                base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
                llm_to_use = ChatOllama(model=model_name, temperature=0.0, base_url=base_url)

        llm_out = llm_to_use.invoke(messages)
        answer_text = getattr(llm_out, "content", str(llm_out))

        # Optional calculation engine
        calc_md = try_compute(question)

        # Append calc section if exists
        if calc_md:
            answer_text = f"{answer_text}\n\n### Calculation\n{calc_md}"

        return answer_text, citations, calc_md
