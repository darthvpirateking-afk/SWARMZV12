# SWARMZ — Quickstart Guide

> From zero to running in 5 minutes. Windows-first.

---

## Prerequisites

- **Windows 10/11** (or any OS with Python 3.10+)
- **Python 3.10+** installed and in `PATH`
- Git (optional, for cloning)

## Step 1: Get the Code

```cmd
git clone <your-repo-url> swarmz
cd swarmz
```

Or unzip the folder if you received it as an archive.

## Step 2: Start SWARMZ

### Option A: Double-click (easiest)

Double-click **`SWARMZ_UP.cmd`** in the project folder.

This will:
1. Create a Python virtual environment (`venv/`)
2. Install dependencies (`fastapi`, `uvicorn`, `pyjwt`)
3. Check if port 8012 is free
4. Start the server
5. Print your Local + LAN URLs

### Option B: PowerShell

```powershell
.\SWARMZ_UP.ps1
```

### Option C: Manual

```cmd
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m uvicorn server:app --host 0.0.0.0 --port 8012
```

## Step 3: Open the UI

- **On your PC:** Open `http://localhost:8012` in your browser
- **On your phone:** Connect to the same Wi-Fi, then open `http://<LAN_IP>:8012`

The LAN IP is printed when the server starts (e.g., `LAN: http://192.168.1.42:8012/`).

## Step 4: Verify It Works

Run the smoke test:

```cmd
SWARMZ_SMOKE_TEST.cmd
```

Or manually:

```cmd
curl http://localhost:8012/health
```

Expected: `{"status":"ok"}`

## Step 5: Access from Your Phone

1. Make sure your phone is on the **same Wi-Fi** as your PC.
2. Open the LAN URL in your phone browser (e.g., `http://192.168.1.42:8012`).
3. If it doesn't connect, you may need to allow port 8012 through Windows Firewall:

```powershell
# Run PowerShell as Administrator
New-NetFirewallRule -DisplayName "SWARMZ Port 8012" -Direction Inbound -Protocol TCP -LocalPort 8012 -Action Allow
```

Or via GUI: Windows Defender Firewall → Advanced Settings → Inbound Rules → New Rule → Port → TCP 8012 → Allow.

---

## Configuration

All settings live in **`config/runtime.json`**:

| Setting | Default | Purpose |
|---------|---------|---------|
| `port` | 8012 | Server port |
| `bind` | `0.0.0.0` | Bind address (`0.0.0.0` = all interfaces, needed for LAN) |
| `offlineMode` | false | Skip external API calls |
| `models.provider` | `anthropic` | AI model provider |
| `integrations.zapier.enabled` | true | Enable Zapier bridge |

## Diagnostic Tools

| Tool | How to Run |
|------|-----------|
| Doctor | `SWARMZ_DOCTOR.cmd` or `SWARMZ_DOCTOR.ps1` |
| Smoke Test | `SWARMZ_SMOKE_TEST.cmd` or `SWARMZ_SMOKE_TEST.ps1` |
| Zapier Test | `python tools/test_zapier_bridge.py` |
| Full Smoke | `python tools/smoke/run_smoke.py` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8012 in use | Close the other process, or set `KILL_PORT=1` before running `SWARMZ_UP` |
| Phone can't connect | Check same Wi-Fi + firewall rule (see Step 5) |
| `run_swarmz.py` fails | Use `SWARMZ_UP.cmd` instead (known issue with `run_swarmz.py`) |
| Missing dependencies | Delete `venv/` and re-run `SWARMZ_UP.cmd` |
