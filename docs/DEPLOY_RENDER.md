# Deploying NEXUSMON on Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

The `render.yaml` Blueprint at the repo root provisions two Render services in one click:

| Service | Type | What it does |
|---|---|---|
| `nexusmon-api` | Python web service | FastAPI backend served by uvicorn |
| `nexusmon-web` | Static site | Standalone HTML/JS/CSS frontend from `web/` |

---

## Quick deploy (Blueprint)

1. Push this repo to GitHub (or fork it).
2. Open the [Render Dashboard](https://dashboard.render.com) → **New → Blueprint**.
3. Connect the repository — Render detects `render.yaml` and previews both services.
4. Click **Apply**. Render builds and deploys everything automatically.

---

## Manual web-service setup

If you prefer to configure the API service by hand in the dashboard:

| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build command** | `pip install -r requirements.txt` |
| **Start command** | `uvicorn swarmz_server:app --host 0.0.0.0 --port $PORT` |
| **Health check path** | `/health` |

---

## Environment variables

The Blueprint sets these automatically. Review and override them in **Dashboard → nexusmon-api → Environment**.

| Variable | How it's set | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11` | Python version used during the build |
| `ALLOWED_ORIGINS` | `https://nexusmon-web.onrender.com` | Comma-separated CORS origins; update after first deploy if URLs differ |
| `OPERATOR_KEY` | Auto-generated | API key required for operator-gated endpoints — copy from dashboard |
| `JWT_SECRET` | Auto-generated | HS256 secret for signing/verifying JWT tokens |

> `OPERATOR_KEY` and `JWT_SECRET` are generated once by Render and stored as encrypted secrets. You can rotate them in the dashboard at any time.

---

## Persistent disk for `data/`

NEXUSMON writes conversation history, trial records, and other runtime state as JSONL files under `data/`. The Blueprint attaches a **1 GB persistent disk** mounted at `/opt/render/project/src/data` so this state survives deploys and restarts.

> **Paid plan required.** Render's free tier does not support persistent disks. You need the **Starter** plan or above to use this feature.

---

## Verifying the deployment

Once the deploy turns green, hit the auto-generated API docs:

```
https://nexusmon-api.onrender.com/docs
```

Or check the health endpoint:

```bash
curl https://nexusmon-api.onrender.com/health
# → {"ok": true, "status": "ok"}
```

---

## Connecting the frontend to the API

After both services are live, update `ALLOWED_ORIGINS` in `nexusmon-api` to include the exact URL of `nexusmon-web` (shown in the Static Site dashboard), then redeploy. In `web/app.js` set the base URL constant to your `nexusmon-api` Render URL.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails with `ModuleNotFoundError` | Ensure all imports are covered in `requirements.txt` and redeploy |
| `/health` returns 502 | Service may still be starting; wait 60 s then retry. Check **Logs** tab |
| CORS errors in browser | Add the frontend origin to `ALLOWED_ORIGINS` and redeploy the API service |
| Data lost after redeploy | Persistent disk not attached — upgrade to a paid plan and verify the disk is mounted |
| `JWT_SECRET` errors | Set `JWT_SECRET` to a random string ≥ 32 chars in the environment dashboard |
