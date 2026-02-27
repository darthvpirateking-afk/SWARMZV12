from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class TemplateSyncManager:
    def __init__(self, root_dir: Path):
        self._root = root_dir
        self._base = root_dir / "data" / "template_sync"
        self._base.mkdir(parents=True, exist_ok=True)

        self._config_path = self._base / "config.json"
        self._jobs_path = self._base / "jobs.jsonl"
        self._templates_path = self._base / "templates.jsonl"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        out: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
        return out

    def _default_config(self) -> Dict[str, Any]:
        return {
            "operator_id": "",
            "allowlist": [],
            "auto_sync": False,
            "sync_interval_hours": 24,
            "created_at": self._now(),
            "updated_at": self._now(),
        }

    def get_config(self) -> Dict[str, Any]:
        if not self._config_path.exists():
            cfg = self._default_config()
            self._config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            return cfg
        try:
            payload = json.loads(self._config_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        cfg = self._default_config()
        self._config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return cfg

    def update_config(
        self,
        operator_id: str,
        allowlist: Optional[List[str]] = None,
        auto_sync: Optional[bool] = None,
        sync_interval_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        cfg = self.get_config()
        cfg["operator_id"] = operator_id.strip()
        if allowlist is not None:
            cfg["allowlist"] = [
                entry.strip() for entry in allowlist if entry and entry.strip()
            ]
        if auto_sync is not None:
            cfg["auto_sync"] = bool(auto_sync)
        if sync_interval_hours is not None:
            cfg["sync_interval_hours"] = max(1, int(sync_interval_hours))
        cfg["updated_at"] = self._now()
        self._config_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return cfg

    def queue_sync(
        self,
        operator_id: str,
        source_url: str,
        template_name: str,
        dry_run: bool = True,
        notes: str = "",
    ) -> Dict[str, Any]:
        cfg = self.get_config()

        bound_operator = str(cfg.get("operator_id", "")).strip()
        if not bound_operator:
            return {"error": "operator_not_bound"}
        if operator_id.strip() != bound_operator:
            return {"error": "operator_mismatch"}

        allowlist = cfg.get("allowlist", [])
        if not any(source_url.startswith(prefix) for prefix in allowlist):
            return {"error": "source_not_allowlisted"}

        mode = "dry_run" if dry_run else "queued"
        job = {
            "job_id": f"sync-{secrets.token_hex(4)}",
            "operator_id": operator_id,
            "source_url": source_url,
            "template_name": template_name,
            "mode": mode,
            "notes": notes,
            "status": "planned" if dry_run else "queued_for_worker",
            "created_at": self._now(),
        }
        self._append_jsonl(self._jobs_path, job)

        if dry_run:
            return {
                "ok": True,
                "job": job,
                "message": "Dry-run only. No remote fetch executed.",
            }

        record = {
            "template_id": f"tpl-{secrets.token_hex(4)}",
            "template_name": template_name,
            "source_url": source_url,
            "operator_id": operator_id,
            "status": "linked",
            "created_at": self._now(),
        }
        self._append_jsonl(self._templates_path, record)
        return {"ok": True, "job": job, "template": record}

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._jobs_path)
        return rows[-max(1, min(limit, 500)) :]

    def list_templates(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._read_jsonl(self._templates_path)
        return rows[-max(1, min(limit, 500)) :]
