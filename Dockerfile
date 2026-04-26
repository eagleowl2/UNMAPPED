FROM python:3.11-slim

LABEL maintainer="UNMAPPED Protocol Team"
LABEL description="UNMAPPED SSE — Skills Signal Engine v0.3.1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    CORS_ORIGINS="http://localhost:3000,http://localhost:5173,http://localhost:8080,http://frontend:5173" \
    # HuggingFace cache inside the image — model is baked at build time
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    # Suppress symlink warning on Windows hosts when running tests locally
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

WORKDIR /app

# System deps: curl (healthcheck) + git (HF hub uses it for clones)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first (~250 MB vs ~2 GB GPU default).
# requirements.txt has `torch>=2.2.0`; installing from the CPU wheel
# index satisfies that pin without pulling CUDA.
RUN pip install --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

# Install remaining deps (torch already satisfied, won't be reinstalled).
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy multilingual model
RUN python -m spacy download xx_ent_wiki_sm

# Pre-bake the multilingual-e5-small model so the first demo parse is
# instant. ~118 MB baked into the image layer.
RUN python -c "\
from transformers import AutoTokenizer, AutoModel; \
AutoTokenizer.from_pretrained('intfloat/multilingual-e5-small'); \
AutoModel.from_pretrained('intfloat/multilingual-e5-small'); \
print('multilingual-e5-small cached OK')"

COPY . .

# Non-root user for safer container execution
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
