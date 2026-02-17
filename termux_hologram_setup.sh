#!/data/data/com.termux/files/usr/bin/bash
# SWARMZ Hologram Termux Setup Script
# Sets up Python environment for the hologram system on Android via Termux

echo "========================================"
echo "SWARMZ Hologram - Termux Setup (Android)"
echo "========================================"
echo ""

# Update package list
echo "Updating Termux packages..."
pkg update -y

# Install Python and essential tools
echo "Installing Python and dependencies..."
pkg install -y python python-pip

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install SWARMZ hologram dependencies
echo "Installing SWARMZ hologram requirements..."
pip install -r swarmz_runtime_requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies"
    echo "Please check your internet connection and try again"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ SWARMZ Hologram setup complete!"
echo "========================================"
echo ""
echo "To start the hologram server, run:"
echo "  ./termux_hologram_run.sh"
echo ""