# SWARMZ Runtime Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Build frontend assets (optional - continue on failure)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends nodejs npm \
	&& rm -rf /var/lib/apt/lists/*

COPY . .

# Build frontend if directory exists, but don't fail if build fails
RUN if [ -d "frontend" ]; then \
		cd frontend && (npm ci && npm run build || echo "Frontend build failed, continuing..."); \
	fi

# Ensure web directory exists
RUN ls -la web/ || echo "Warning: web/ directory not found"

EXPOSE 8000

CMD ["sh", "-c", "uvicorn swarmz_server:app --host 0.0.0.0 --port ${PORT:-8000}"]
