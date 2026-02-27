# ── NEXUSMON backend ──────────────────────────────────────────────────────────
# Builds a production-ready image for the FastAPI / Uvicorn service.
# Entry point: swarmz_server:app
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
# curl  → used by HEALTHCHECK CMD
# build-essential / libpq-dev → common native-extension build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Snapshot directory ────────────────────────────────────────────────────────
# HologramReconciler resolves HLOG_SNAPSHOT_DIR at import time.
# We create the path and expose it as a volume so it survives restarts.
ENV HLOG_SNAPSHOT_DIR=/var/lib/nexusmon/hologram_snapshots

RUN mkdir -p /var/lib/nexusmon/hologram_snapshots

# ── Non-root user ─────────────────────────────────────────────────────────────
# python:3.11-slim doesn't guarantee stable nobody UID/GID across rebuilds;
# add a dedicated system user instead.
RUN addgroup --system nexusmon \
    && adduser --system --ingroup nexusmon --no-create-home nexusmon \
    && chown -R nexusmon:nexusmon /var/lib/nexusmon

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first for better layer caching.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# ── Volume hint ───────────────────────────────────────────────────────────────
# Docker Engine records this as metadata; override in compose / k8s as needed.
VOLUME ["/var/lib/nexusmon/hologram_snapshots"]

# ── Runtime user ──────────────────────────────────────────────────────────────
USER nexusmon

# ── Port ─────────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Health check ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Entry point ───────────────────────────────────────────────────────────────
# Override workers / loop in compose or k8s via CMD or ENTRYPOINT extension.
CMD ["uvicorn", "swarmz_server:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop"]
