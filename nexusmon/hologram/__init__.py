"""nexusmon.hologram — Hologram state engine for NEXUSMON.

Subsystems:
    HologramIngestor    — Subscribes to FeedStream, normalizes events into typed ops.
    HologramReconciler  — Threaded loop: applies batched ops, EWMA health, snapshots.
    HologramPublisher   — Fan-out pub/sub for diff and snapshot events.
    create_hologram_api — FastAPI sub-app: /snapshot/latest, /patch, /ws.
    bootstrap_hologram  — Wire all subsystems together and optionally mount on app.
"""

from nexusmon.hologram.hologram_ingestor import HologramIngestor
from nexusmon.hologram.hologram_reconciler import HologramReconciler, HologramPublisher
from nexusmon.hologram.hologram_api import create_hologram_api
from nexusmon.hologram.hologram_bootstrap import bootstrap_hologram

__all__ = [
    "HologramIngestor",
    "HologramReconciler",
    "HologramPublisher",
    "create_hologram_api",
    "bootstrap_hologram",
]
