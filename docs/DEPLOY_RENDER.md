# Deploying NEXUSMON on Render

This guide explains how to deploy NEXUSMON on [Render](https://render.com) using the included Blueprint file (`render.yaml`).

## Services

The `render.yaml` Blueprint defines two services:

| Service | Type | Description |
|---|---|---|
| `nexusmon-api` | Python web service | FastAPI backend (uvicorn) |
| `nexusmon-web` | Static site | Frontend UI from `web/` |

## Quick Deploy

1. Fork or push this repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New → Blueprint**.
3. Connect your GitHub repository.
4. Render will detect `render.yaml` and create both services automatically.

## Manual Service Setup

If you prefer to create the web service manually:

- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn swarmz_server:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

## Persistent Disk for `data/`

NEXUSMON stores runtime state as JSONL files under the `data/` directory. The Blueprint attaches a **1 GB persistent disk** mounted at `/opt/render/project/src/data` (the `data/` subdirectory of the service's working directory). This ensures that conversation history, trial records, and other runtime artifacts survive service restarts and re-deploys.

> **Note**: Render's free tier does not support persistent disks. Upgrade to a paid plan (Starter or above) to use this feature.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11` | Python version for the build environment |
| `PORT` | `10000` | Port Render injects automatically at runtime |

You may also set optional variables such as `ALLOWED_ORIGINS` (comma-separated CORS origins) depending on your configuration.

## Verifying the Deployment

Once the service is live, confirm it is running by visiting the interactive API docs:

```
https://<your-service-name>.onrender.com/docs
```

You can also hit the health endpoint directly:

```bash
curl https://<your-service-name>.onrender.com/health
# Expected: {"ok": true, "status": "ok"}
```

## Static Frontend (`nexusmon-web`)

The `web/` directory contains a standalone HTML/JS/CSS frontend. The Blueprint publishes it as a Render Static Site with a catch-all rewrite to `index.html` for client-side routing.

Point the frontend at the API by setting the backend URL in your environment or by updating `web/app.js` to use the deployed API URL.
