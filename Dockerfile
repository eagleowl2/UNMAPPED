FROM python:3.11-slim

LABEL maintainer="UNMAPPED Protocol Team"
LABEL description="UNMAPPED SSE — Skills Signal Engine v0.3-sse-alpha.1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    CORS_ORIGINS="http://localhost:3000,http://localhost:5173"

WORKDIR /app

# System deps for spaCy + tokenizers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy multilingual model
RUN python -m spacy download xx_ent_wiki_sm

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
