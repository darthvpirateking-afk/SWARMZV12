#!/data/data/com.termux/files/usr/bin/bash
# SWARMZ Hologram Termux Run Script
# Starts the SWARMZ hologram server on Android

echo "========================================"
echo "⚡ SWARMZ Hologram - Starting Server"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed"
    echo "Please run ./termux_hologram_setup.sh first"
    exit 1
fi

# Check if dependencies are installed
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Dependencies not installed"
    echo "Installing dependencies..."
    pip install -r swarmz_runtime_requirements.txt
    echo ""
fi

# Get IP address for display
IP_ADDR=$(ifconfig 2>/dev/null | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -n1)

echo "📱 Running SWARMZ Hologram on Android via Termux"
echo ""
echo "📡 Access SWARMZ Hologram at:"
echo "   Local:  http://localhost:8020"
if [ -n "$IP_ADDR" ]; then
    echo "   LAN:    http://$IP_ADDR:8020"
fi
echo ""
echo "💡 Open the URL in your mobile browser"
echo "📱 Tap 'Add to Home Screen' to install as an app"
echo ""
echo "Press Ctrl+C to stop the server"

# Start the hologram server
python run_hologram.py --host 0.0.0.0 --port 8020