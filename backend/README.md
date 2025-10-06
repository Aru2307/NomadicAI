# Backend

Run locally:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Data directories:
- `backend/data/uploads`
- `backend/data/chroma`

APIs:
- `GET /health`
- `POST /upload` (multipart `files`)
- `POST /ask` { question }
