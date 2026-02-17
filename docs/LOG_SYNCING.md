# Log Syncing

This document explains how to sync SWARMZ logs to a remote mirror.

## Supported Methods
- SFTP
- rsync
- ZIP export (fallback)

## Fail-Open Principle
If syncing fails, SWARMZ will skip the operation silently.