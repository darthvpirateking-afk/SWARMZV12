# Bridge Migration Status

## Static Mount Fix
- Status: COMPLETE
- Changed: `swarmz_runtime/api/server.py`
- Preserved: `/static` compatibility (conditional mount)
- Added: `/ui` cockpit path (conditional mount)
- Validated: server import no longer hard-fails when static directories are absent

## Legacy Ollama Fragment
- Status: COMPLETE
- Removed: `/_call_ollama.py`
- Direct imports removed: none found

## Canonical Bridge
- Status: COMPLETE
- Added package: `swarmz_runtime/bridge/`
- Added adapters: OpenAI, Groq, vLLM stub (disabled by default in runtime config)

## Payment Webhook Hardening
- Status: COMPLETE
- Endpoint: `POST /v1/store/payment-webhook` hardened in place.
- Added: HMAC signature verification (`X-Webhook-Signature`) + fail-closed secret checks.
- Added: idempotency tracking at `data/payments/processed_events.jsonl`.
- Added: security events `forged_webhook` and `webhook_replay`.

## Cloud Secret Setup
- Status: COMPLETE
- Set `PAYMENT_WEBHOOK_SECRET` in cloud dashboards before enabling Stripe/Paddle/LemonSqueezy:
  - Render: Service → Environment
  - Fly.io: `fly secrets set PAYMENT_WEBHOOK_SECRET=...`
  - Railway: Variables → `PAYMENT_WEBHOOK_SECRET`

## Pending Consumer Migrations
- `core/model_router.py` still owns legacy provider routing (intentionally unchanged in this pass).
- Runtime callers in `core/` remain on existing flow until the next migration pass.
