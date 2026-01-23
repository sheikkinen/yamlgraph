FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    yamlgraph \
    feedparser \
    resend \
    beautifulsoup4 \
    httpx \
    fastapi \
    slowapi \
    uvicorn \
    python-multipart \
    python-dotenv

# Copy application code
COPY . .

# Use /data for SQLite (mounted volume on Fly.io)
ENV DATABASE_PATH=/data/digest.db

# Expose port
EXPOSE 8080

# Run FastAPI server
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8080"]
