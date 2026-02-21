# SWARMZ Runtime Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Node for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build frontend
RUN cd frontend && npm ci && npm run build

EXPOSE 8012

CMD ["sh", "-c", "alembic upgrade head 2>/dev/null || true && python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8012} --log-level info"]
