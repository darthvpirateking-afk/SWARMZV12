#!/data/data/com.termux/files/usr/bin/bash
# SWARMZ Termux Setup Script
# Sets up Python environment on Android via Termux

echo "========================================"
echo "SWARMZ - Termux Setup (Android)"
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

# Install SWARMZ dependencies
echo "Installing SWARMZ requirements..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install dependencies"
    echo "Please check your internet connection and try again"
    exit 1
fi

echo ""
echo "========================================"
echo "✓ SWARMZ setup complete!"
echo "========================================"
echo ""
echo "To start the server, run:"
echo "  ./termux_run.sh"
echo ""
echo "Or manually:"
echo "  python swarmz_server.py"
echo ""
