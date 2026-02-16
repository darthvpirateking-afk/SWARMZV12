#!/usr/bin/env bash
# SWARMZ — Single-file Install & Run
# Creates venv → installs deps → runs server → opens browser → prints LAN URL + QR
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${SCRIPT_DIR}/venv"
PORT="${SWARMZ_API_PORT:-8012}"
HOST="0.0.0.0"

echo "=============================================="
echo "  SWARMZ — Install & Run"
echo "=============================================="

# 1. Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "[1/4] Creating virtual environment..."
  python3 -m venv "$VENV_DIR"
else
  echo "[1/4] Virtual environment exists — skipping"
fi

# 2. Install deps
echo "[2/4] Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r requirements.txt
# qrcode is optional; install if possible
"$VENV_DIR/bin/pip" install --quiet qrcode 2>/dev/null || true

# 3. Detect LAN IP
LAN_IP="127.0.0.1"
if command -v hostname &>/dev/null; then
  CANDIDATE=$(hostname -I 2>/dev/null | awk '{print $1}')
  [ -n "$CANDIDATE" ] && LAN_IP="$CANDIDATE"
fi
LAN_URL="http://${LAN_IP}:${PORT}"

# 4. Print LAN URL + QR code
echo ""
echo "=============================================="
echo "  LAN URL:  $LAN_URL"
echo "  Docs:     $LAN_URL/docs"
echo "  Dashboard: $LAN_URL/dashboard"
echo "=============================================="

# Attempt QR code
"$VENV_DIR/bin/python" -c "
try:
    import qrcode, sys
    qr = qrcode.QRCode(box_size=1, border=1)
    qr.add_data('${LAN_URL}/dashboard')
    qr.make(fit=True)
    qr.print_ascii(invert=True)
except Exception:
    print('(Install qrcode package for QR display)')
" 2>/dev/null || echo "(QR code display unavailable)"

echo ""

# 5. Open browser (best-effort)
if command -v xdg-open &>/dev/null; then
  xdg-open "$LAN_URL/dashboard" 2>/dev/null &
elif command -v open &>/dev/null; then
  open "$LAN_URL/dashboard" 2>/dev/null &
fi

# 6. Run server
echo "Starting SWARMZ server on ${HOST}:${PORT} ..."
exec "$VENV_DIR/bin/python" -m uvicorn swarmz_runtime.api.server:app --host "$HOST" --port "$PORT"
