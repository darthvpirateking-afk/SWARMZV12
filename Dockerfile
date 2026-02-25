# SWARMZ Runtime Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend assets
RUN apt-get update \
	&& apt-get install -y --no-install-recommends nodejs npm \
	&& rm -rf /var/lib/apt/lists/*

COPY . .

RUN cd frontend && npm ci && npm run build

EXPOSE 8000

CMD ["sh", "-c", "uvicorn swarmz_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
