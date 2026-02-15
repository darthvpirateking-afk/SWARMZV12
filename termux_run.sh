#!/data/data/com.termux/files/usr/bin/bash
# termux_run.sh — Start the SWARMZ server on Termux (Android)
#
# Usage:
#   bash termux_run.sh

set -e

echo "============================================"
echo "  SWARMZ — Starting on Termux"
echo "============================================"
echo ""

python run_swarmz.py
