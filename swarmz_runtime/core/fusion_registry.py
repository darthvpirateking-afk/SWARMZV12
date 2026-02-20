from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class FusionRegistry:
    """Immutable-ish provenance registry with hash chaining for idea ownership and lineage."""

    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._base = root_dir / "data" / "fusion"
        self._base.mkdir(parents=True, exist_ok=True)
        self._registry = self._base / "idea_registry.jsonl"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows

    @staticmethod
    def _append_jsonl(path: Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    @staticmethod
    def _hash_payload(prev_hash: str, payload: Dict[str, Any]) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256((prev_hash + normalized).encode("utf-8")).hexdigest()

    def register(
        self,
        title: str,
        owner: str,
        source: str,
        summary: str,
        tags: Optional[List[str]] = None,
        linked_docs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        rows = self._read_jsonl(self._registry)
        prev_hash = rows[-1]["hash"] if rows else "genesis"

        payload = {
            "entry_id": f"fuse-{secrets.token_hex(4)}",
            "title": title,
            "owner": owner,
            "source": source,
            "summary": summary,
            "tags": tags or [],
            "linked_docs": linked_docs or [],
            "created_at": self._now(),
            "index": len(rows) + 1,
        }
        entry_hash = self._hash_payload(prev_hash, payload)
        entry = {"payload": payload, "prev_hash": prev_hash, "hash": entry_hash}
        self._append_jsonl(self._registry, entry)
        return entry

    def list_entries(self) -> List[Dict[str, Any]]:
        return self._read_jsonl(self._registry)

    def verify_chain(self) -> Dict[str, Any]:
        rows = self._read_jsonl(self._registry)
        prev_hash = "genesis"
        for idx, row in enumerate(rows, start=1):
            payload = row.get("payload", {})
            expected = self._hash_payload(prev_hash, payload)
            if row.get("hash") != expected:
                return {
                    "ok": False,
                    "valid": False,
                    "failed_index": idx,
                    "reason": "hash_mismatch",
                }
            prev_hash = row.get("hash", "")
        return {
            "ok": True,
            "valid": True,
            "count": len(rows),
            "head_hash": prev_hash if rows else "genesis",
        }

    def summary(self) -> Dict[str, Any]:
        rows = self._read_jsonl(self._registry)
        by_owner: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        tags: Dict[str, int] = {}

        for row in rows:
            payload = row.get("payload", {})
            owner = str(payload.get("owner", "unknown"))
            source = str(payload.get("source", "unknown"))
            by_owner[owner] = by_owner.get(owner, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
            for tag in payload.get("tags", []):
                tags[str(tag)] = tags.get(str(tag), 0) + 1

        return {
            "ok": True,
            "entries": len(rows),
            "owners": by_owner,
            "sources": by_source,
            "top_tags": sorted(tags.items(), key=lambda kv: kv[1], reverse=True)[:10],
            "chain": self.verify_chain(),
        }
