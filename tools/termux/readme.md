# Termux Scripts for SWARMZ

## Scripts

1. **start-swarmz.sh**: Activates the virtual environment and starts the Uvicorn server.
2. **termux-boot.sh**: Configured to run on Termux:Boot to start the server automatically on device boot.

## Setup

1. Install Termux and Termux:Boot from F-Droid.
2. Place these scripts in the `tools/termux/` directory.
3. Grant execute permissions: `chmod +x start-swarmz.sh termux-boot.sh`.
4. Ensure Termux:Boot is configured to run `termux-boot.sh` on boot.

## Logs

Logs are stored in `logs/termux_server.log`.