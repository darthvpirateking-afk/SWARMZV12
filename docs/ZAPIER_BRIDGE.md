# NEXUSMON :: Zapier Universal Connector Bridge

## Overview

The Zapier bridge gives NEXUSMON a **universal integration pipe**:

| Direction | Flow |
|-----------|------|
| **Inbound** | Any Zapier trigger → Webhooks POST → NEXUSMON creates a mission |
| **Outbound** | NEXUSMON emits JSON → Zapier Catch Hook → any app action |

---

## Configuration

Edit **`config/runtime.json`** — look for the `integrations.zapier` block:

```json
"integrations": {
  "zapier": {
    "enabled": true,
    "shared_secret": "change-me-to-a-real-secret",
    "inbound_path": "/v1/zapier/inbound",
    "emit_path": "/v1/zapier/emit",
    "zapier_catch_hook_url": ""
  }
}
```

| Key | Purpose |
|-----|---------|
| `enabled` | `false` → endpoints return safe "disabled" response |
| `shared_secret` | Shared between NEXUSMON and your Zaps. Pass as `X-NEXUSMON-SECRET` header. |
| `inbound_path` | URL path for Zapier → NEXUSMON triggers (default `/v1/zapier/inbound`) |
| `emit_path` | URL path for NEXUSMON → Zapier emits (default `/v1/zapier/emit`) |
| `zapier_catch_hook_url` | Paste your Zapier Catch Hook URL here. If empty, `/emit` returns `ok:false`. |

---

## Zap #1: Any App Trigger → NEXUSMON Mission

**Goal:** When *anything* happens in Zapier (new email, Slack message, form submission, etc.), create a NEXUSMON mission.

### Setup Steps

1. In Zapier, create a new Zap.
2. **Trigger:** Pick any app + event (e.g., Gmail → New Email).
3. **Action:** Choose **Webhooks by Zapier → POST**.
4. Configure:
   - **URL:** `http://<YOUR_LAN_IP>:8012/v1/zapier/inbound`
   - **Payload Type:** JSON
   - **Data:**
     ```
     source: zapier
     type: trigger.gmail.new_email
     payload.subject: {{subject}}
     payload.from: {{from}}
     dedupe_key: {{message_id}}
     ```
   - **Headers:**
     ```
     X-NEXUSMON-SECRET: change-me-to-a-real-secret
     ```
5. Test the Zap and confirm a mission appears in NEXUSMON.

> **Note:** For LAN access from Zapier, you need your PC reachable from the internet (e.g., ngrok). For local testing, use the test commands below.

---

## Zap #2: NEXUSMON → Any App Action (via Catch Hook)

**Goal:** When NEXUSMON emits a notice, Zapier picks it up and runs any action (send email, post to Slack, update sheet, etc.).

### Setup Steps

1. In Zapier, create a new Zap.
2. **Trigger:** Choose **Webhooks by Zapier → Catch Hook**.
3. Copy the Catch Hook URL Zapier gives you.
4. Paste it into `config/runtime.json`:
   ```json
   "zapier_catch_hook_url": "https://hooks.zapier.com/hooks/catch/12345/abcdef/"
   ```
5. **Action:** Pick any app (e.g., Slack → Send Message).
6. Map fields from the caught payload.
7. Test by calling the emit endpoint (see below).

---

## Example Payloads

### Inbound (Zapier → NEXUSMON)

```json
{
  "source": "zapier",
  "type": "trigger.gmail.new_email",
  "payload": {
    "subject": "Weekly Report",
    "from": "boss@example.com"
  },
  "dedupe_key": "msg-12345"
}
```

### Outbound (NEXUSMON → Zapier)

```json
{
  "type": "nexusmon.mission_complete",
  "payload": {
    "mission_id": "mission_1739753400000",
    "status": "SUCCESS",
    "summary": "Task completed"
  }
}
```

---

## Test Commands

### Windows CMD

```cmd
REM Test inbound
curl -X POST http://localhost:8012/v1/zapier/inbound -H "Content-Type: application/json" -H "X-NEXUSMON-SECRET: change-me-to-a-real-secret" -d "{\"source\":\"zapier\",\"type\":\"trigger.test.smoke\",\"payload\":{\"msg\":\"hello from CMD\"},\"dedupe_key\":\"test-cmd-1\"}"

REM Test emit (no hook URL → returns ok:false, which is expected)
curl -X POST http://localhost:8012/v1/zapier/emit -H "Content-Type: application/json" -H "X-NEXUSMON-SECRET: change-me-to-a-real-secret" -d "{\"type\":\"nexusmon.test\",\"payload\":{\"msg\":\"emit from CMD\"}}"
```

### Windows PowerShell

```powershell
# Test inbound
$headers = @{ "Content-Type" = "application/json"; "X-NEXUSMON-SECRET" = "change-me-to-a-real-secret" }
$body = '{"source":"zapier","type":"trigger.test.smoke","payload":{"msg":"hello from PS"},"dedupe_key":"test-ps-1"}'
Invoke-WebRequest -Uri "http://localhost:8012/v1/zapier/inbound" -Method POST -Headers $headers -Body $body -UseBasicParsing | Select-Object -ExpandProperty Content

# Test emit
$emitBody = '{"type":"nexusmon.test","payload":{"msg":"emit from PS"}}'
Invoke-WebRequest -Uri "http://localhost:8012/v1/zapier/emit" -Method POST -Headers $headers -Body $emitBody -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## Logs

All events are appended (never overwritten) to:

| File | Content |
|------|---------|
| `data/zapier/inbound.jsonl` | Every inbound trigger received |
| `data/zapier/outbound.jsonl` | Every outbound emit attempted |

Each log line includes: `ts`, `direction`, `event_id`, `source`, `type`, `payload`, `ok`, `error`.

---

## Security

- **Do NOT expose your NEXUSMON instance to the public internet** without additional protection.
- The `shared_secret` header provides basic authentication for the bridge.
- For production use with Zapier cloud, tunnel via ngrok or similar.

