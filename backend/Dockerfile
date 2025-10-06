# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps for unstructured and pdf parsing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libmagic1 \
    tesseract-ocr \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend

ENV PYTHONPATH=/app

EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
