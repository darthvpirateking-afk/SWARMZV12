# SWARMZ NEXUSMON — The Sensorium: Substrate Awareness Bridge
# ─────────────────────────────────────────────────────────
import psutil
import time
import threading
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class Sensorium:
    """Hardware mapping bridge that feeds substrate telemetry into the Nerve Center."""

    def __init__(self, nerve_instance):
        self.nerve = nerve_instance
        self.active = False
        self.thread = None
        self.poll_interval = 5.0  # seconds

        # Baselines
        self.prev_net_io = psutil.net_io_counters()

    def start(self):
        """Starts the background telemetry polling loop."""
        if self.active:
            return
        self.active = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("[SENSORIUM] Substrate Awareness Active.")

    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join(timeout=1.0)
        logger.info("[SENSORIUM] Substrate Awareness Terminated.")

    def _loop(self):
        while self.active:
            try:
                stats = self._gather_telemetry()
                self._process_signals(stats)
            except Exception as e:
                logger.error(f"[SENSORIUM] Telemetry error: {e}")
            time.sleep(self.poll_interval)

    def _gather_telemetry(self) -> Dict:
        # CPU
        cpu_pct = psutil.cpu_percent(interval=None)

        # RAM
        mem = psutil.virtual_memory()
        mem_pct = mem.percent

        # Disk
        disk = psutil.disk_usage("/")
        disk_pct = disk.percent

        # Network Delta
        curr_net = psutil.net_io_counters()
        net_delta_sent = curr_net.bytes_sent - self.prev_net_io.bytes_sent
        net_delta_recv = curr_net.bytes_recv - self.prev_net_io.bytes_recv
        self.prev_net_io = curr_net

        return {
            "cpu": cpu_pct,
            "mem": mem_pct,
            "disk": disk_pct,
            "net_sent": net_delta_sent,
            "net_recv": net_delta_recv,
        }

    def _process_signals(self, stats: Dict):
        # 1. Stress Evaluation
        if stats["cpu"] > 80.0:
            self.nerve.fire(
                "SENSORIUM",
                "STRESS",
                payload={"cause": "CPU_PEAK", "val": stats["cpu"]},
                intensity=2.0,
            )

        if stats["mem"] > 85.0:
            self.nerve.fire(
                "SENSORIUM",
                "STRESS",
                payload={"cause": "MEM_PEAK", "val": stats["mem"]},
                intensity=1.5,
            )

        # 2. Synergy Evaluation (Tranquility / Optimal Throughput)
        if stats["cpu"] < 20.0 and stats["mem"] < 50.0:
            self.nerve.fire(
                "SENSORIUM", "SYNERGY", payload={"state": "TRANQUIL"}, intensity=0.5
            )

        if stats["net_recv"] > 1024 * 1024:  # > 1MB of download
            self.nerve.fire(
                "SENSORIUM",
                "SYNERGY",
                payload={"state": "DATA_ABSORPTION", "bits": stats["net_recv"]},
                intensity=1.0,
            )

        # Update Nerve with raw telemetry (optional extended payload)
        # self.nerve.fire("TELEMETRY", "UPDATE", payload=stats, intensity=0.1)


def integrate_sensorium(nerve_instance) -> Sensorium:
    s = Sensorium(nerve_instance)
    s.start()
    return s
