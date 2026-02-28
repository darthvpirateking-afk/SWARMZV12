"""Manifest watcher with schema validation and hot-reload callbacks."""
from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from core.manifest_audit import ManifestAuditLogger
from core.registry import registry

logger = logging.getLogger(__name__)


class ManifestWatcher:
    def __init__(
        self,
        manifests_path: str = "config/manifests",
        poll_seconds: float = 2.0,
        ci_status_path: str = "artifacts/manifest-validation-status.json",
        audit_logger: ManifestAuditLogger | None = None,
    ) -> None:
        self._manifests_path = Path(manifests_path)
        self._poll_seconds = poll_seconds
        self._ci_status_path = ci_status_path
        self._audit = audit_logger or ManifestAuditLogger()
        self._listeners: list[Callable[[str, str, dict[str, Any]], None]] = []
        self._mtimes: dict[str, float] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def add_listener(self, callback: Callable[[str, str, dict[str, Any]], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, str, dict[str, Any]], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self.poll_once()
            self._stop_event.wait(self._poll_seconds)

    def _current_sha(self) -> str:
        env_sha = os.getenv("GITHUB_SHA", "")
        if env_sha:
            return env_sha
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def _maybe_post_pr_comment(self, filename: str, error: str, suggested_fix: str) -> None:
        if os.getenv("GITHUB_EVENT_NAME") != "pull_request":
            return
        try:
            subprocess.run(
                [
                    "python",
                    "tools/post_manifest_failure_comment.py",
                    "--manifest",
                    filename,
                    "--error",
                    error,
                    "--suggested-fix",
                    suggested_fix,
                ],
                check=False,
            )
        except Exception:
            logger.exception("failed to invoke PR failure commenter")

    def poll_once(self) -> None:
        self._manifests_path.mkdir(parents=True, exist_ok=True)
        for file_path in sorted(self._manifests_path.glob("*.json")):
            mtime = file_path.stat().st_mtime
            key = str(file_path)
            last_mtime = self._mtimes.get(key)
            if last_mtime is not None and mtime <= last_mtime:
                continue

            self._mtimes[key] = mtime
            try:
                manifest = json.loads(file_path.read_text(encoding="utf-8-sig"))
            except Exception as exc:
                logger.error("manifest parse failed for %s: %s", file_path.name, exc)
                self._maybe_post_pr_comment(file_path.name, str(exc), "Fix invalid JSON syntax.")
                continue

            manifest_id = str(manifest.get("id", ""))
            errors = registry.validate_manifest(manifest, source=file_path.name)
            if errors:
                logger.error("manifest invalid: %s", "; ".join(errors))
                self._audit.log_manifest_update(
                    actor="watcher",
                    manifest_id=manifest_id or file_path.name,
                    old_value=None,
                    new_value=manifest,
                    trace_id=f"manifest-watch-{int(time.time())}",
                    outcome="failure",
                    full_trace={"errors": errors},
                )
                self._maybe_post_pr_comment(file_path.name, errors[0], "Update fields to match schemas/agent-manifest.v1.json.")
                continue

            old_manifest = registry.get(manifest_id)
            trace_id = f"manifest-watch-{int(time.time())}"
            for callback in list(self._listeners):
                try:
                    callback("manifest.updated", manifest_id, manifest)
                except Exception:
                    logger.exception("manifest watcher listener failed")

            applied_manifest = registry.get(manifest_id)
            outcome = "success" if applied_manifest == manifest else "failure"
            self._audit.log_manifest_update(
                actor="watcher",
                manifest_id=manifest_id,
                old_value=old_manifest,
                new_value=manifest,
                trace_id=trace_id,
                outcome=outcome,
                full_trace=None if outcome == "success" else {"reason": "hot update blocked by CI gate"},
            )
            if outcome != "success":
                logger.warning("manifest update event emitted but not applied for %s", manifest_id)


def attach_registry_hot_reload(watcher: ManifestWatcher) -> None:
    def _listener(event_name: str, manifest_id: str, manifest: dict[str, Any]) -> None:
        if event_name != "manifest.updated":
            return
        registry.handle_manifest_updated(
            manifest_id=manifest_id,
            manifest=manifest,
            actor="watcher-listener",
            ci_status_path=watcher._ci_status_path,
        )

    watcher.add_listener(_listener)
