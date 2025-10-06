# AI Copilot for Engineers (MVP)

Local-first RAG assistant that ingests technical documents (PDF/DOCX/TXT) and answers engineering questions with citations and optional calculations.

## Stack
- Backend: FastAPI, LangChain, ChromaDB, Unstructured/pdfminer, NumPy/SymPy
- Models: OpenAI (if OPENAI_API_KEY set) or local Ollama (llama3.1)
- Frontend: React (Vite + TS)
- Deployment: Docker Compose

## Quick Start (Docker Compose)

1. Option A: Use local Ollama model
   - Docker will run `ollama` service. After containers start, pull model if not present:
     ```bash
     docker exec -it <compose_project>_ollama_1 ollama pull llama3.1
     ```
   - Or set `OPENAI_API_KEY` to use OpenAI instead of Ollama.

2. Start services
   ```bash
   docker compose up --build
   ```

3. Open frontend
   - Visit http://localhost:5173

4. Upload documents and ask questions
   - Use the Upload button to ingest PDFs, DOCX, or TXT
   - Select provider (Auto/OpenAI/Ollama) in the dropdown
   - Ask questions like:
     - "What pipe diameter is needed for this pressure?"
     - "Which material is suitable according to GOST 3262-75?"
     - "Q=2 L/s v=1 m/s" (calc helper will estimate diameter)

## Environment Variables
- `OPENAI_API_KEY` (optional): If set, backend uses OpenAI (gpt-4o-mini, text-embedding-3-small)
- `OLLAMA_MODEL` (optional): Default `llama3.1`
- `OLLAMA_BASE_URL` (optional): Default `http://ollama:11434`

## Dev (without Docker)

- Install Python deps
  ```bash
  pip install -r requirements.txt
  pip install -r backend/requirements.txt
  ```
- Run backend
  ```bash
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
- Run frontend
  ```bash
  cd frontend && npm install && npm run dev
  ```

## Notes
- DWG not supported in MVP; consider converting to PDF/TXT externally.
- All data stays local; ChromaDB persists under `backend/data/chroma`.
- For large PDFs, parsing uses pdfminer via LangChain loader.
