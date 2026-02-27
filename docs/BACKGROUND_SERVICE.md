# Background Service Setup

This document explains how to set up NEXUSMON as a background service.

## Supported Platforms
- Windows
- macOS
- Linux

## Installation
Run the following command:
```bash
python tools/install_service.py
```

## Logs
Service logs are stored in `data/logs/service.log`.

## Fail-Open Principle
If the service manager is unavailable, NEXUSMON will not crash.
