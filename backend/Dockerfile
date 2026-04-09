# ─────────────────────────────────────────────────────────────────────────────
# Backend Dockerfile — Python 3.11 slim
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps (needed for psycopg2-binary + sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache — only re-runs if requirements change)
COPY requirements.txt .

# CPU-only torch saves ~1 GB image size vs default CUDA build
RUN pip install --no-cache-dir torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy source (mounted as volume in dev, so this is mainly for prod builds)
COPY . .

# Pre-download the embedding model so first run is instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 8000

# Default: override via docker-compose command:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]