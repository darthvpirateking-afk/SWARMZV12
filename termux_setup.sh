#!/data/data/com.termux/files/usr/bin/bash
# termux_setup.sh — One-time setup for SWARMZ on Termux (Android)
#
# Usage:
#   pkg install git python -y
#   git clone <repo-url> swarmz && cd swarmz
#   bash termux_setup.sh

set -e

echo "============================================"
echo "  SWARMZ — Termux Setup"
echo "============================================"
echo ""

# 1. Update packages
echo "[1/3] Updating Termux packages …"
pkg update -y && pkg upgrade -y

# 2. Install Python (if missing)
echo "[2/3] Installing Python …"
pkg install python -y

# 3. Install pip dependencies
echo "[3/3] Installing Python dependencies …"
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "  ✓ Setup complete!"
echo "  Run the server with:  bash termux_run.sh"
echo "============================================"
