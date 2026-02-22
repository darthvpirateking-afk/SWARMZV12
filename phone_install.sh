#!/data/data/com.termux/files/usr/bin/bash
# SWARMZ Complete Phone Installation
# Run this in Termux on Android

echo "🤖 ========================================"
echo "🤖 SWARMZ COMPLETE PHONE SETUP"  
echo "🤖 ========================================"
echo ""

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ ERROR: This must be run in Termux app"
    echo "📱 Install Termux from F-Droid first"
    exit 1
fi

echo "📦 Updating Termux packages..."
pkg update -y

echo "🐍 Installing Python and tools..."
pkg install -y python python-pip git curl

echo "⬆️  Upgrading pip..."
pip install --upgrade pip

echo "📚 Installing SWARMZ dependencies..."
pip install fastapi uvicorn python-multipart pydantic

# Check if SWARMZ files exist
if [ ! -f "run_server.py" ]; then
    echo ""
    echo "📁 SWARMZ files not found in current directory"
    echo "📱 Copy the SWARMZ folder to your phone first:"
    echo "   1. Copy entire swarmz folder to phone storage"
    echo "   2. In Termux: cp -r /sdcard/swarmz ~/swarmz"
    echo "   3. cd ~/swarmz"
    echo "   4. Run this script again"
    echo ""
    read -p "📱 Press Enter after copying files..." dummy
fi

echo ""
echo "✅ SWARMZ installation complete!"
echo ""
echo "🚀 To start SWARMZ:"
echo "   python run_server.py"
echo ""
echo "🌐 Then open browser to:"
echo "   http://localhost:8012"
echo ""
echo "🎮 Features available offline:"
echo "   ✅ Full cybernetic interface"
echo "   ✅ Avatar follows finger touches"  
echo "   ✅ 600+ AI personality responses"
echo "   ✅ Voice interface"
echo "   ✅ Mission system"
echo ""
echo "🤖 SWARMZ is now ready on your phone!"