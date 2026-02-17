#!/data/data/com.termux/files/usr/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start Uvicorn server
nohup uvicorn server:app --host 0.0.0.0 --port 8012 > logs/termux_server.log 2>&1 &
echo "SWARMZ server started. Logs are in logs/termux_server.log."