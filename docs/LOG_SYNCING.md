# Log Syncing

This document explains how to sync NEXUSMON logs to a remote mirror.

## Supported Methods
- SFTP
- rsync
- ZIP export (fallback)

## Fail-Open Principle
If syncing fails, NEXUSMON will skip the operation silently.
