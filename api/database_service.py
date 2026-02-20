from datetime import datetime, timezone
from pathlib import Path

from api.database_models import (
    DatabaseCollectionEntry,
    DatabaseCollectionsResponse,
    DatabaseStatsResponse,
    DatabaseStatusResponse,
)
from swarmz_runtime.storage.db import Database


class DatabaseService:
    def __init__(self, data_dir: str = "data") -> None:
        self._db = Database(data_dir=data_dir)
        self._data_dir = Path(data_dir)

    def get_status(self) -> DatabaseStatusResponse:
        return DatabaseStatusResponse(
            ok=True,
            engine="jsonl",
            data_dir=str(self._data_dir),
            generated_at=datetime.now(timezone.utc),
        )

    def get_collections(self) -> DatabaseCollectionsResponse:
        files = [
            ("missions", self._db.missions_file),
            ("audit", self._db.audit_file),
            ("runes", self._db.runes_file),
            ("state", self._db.state_file),
            ("bad_rows", self._data_dir / "bad_rows.jsonl"),
        ]
        collections = []
        for name, path in files:
            exists = path.exists()
            size_bytes = path.stat().st_size if exists else 0
            collections.append(
                DatabaseCollectionEntry(
                    name=name,
                    path=str(path),
                    exists=exists,
                    size_bytes=size_bytes,
                )
            )

        return DatabaseCollectionsResponse(
            ok=True,
            generated_at=datetime.now(timezone.utc),
            collections=collections,
        )

    def get_stats(self) -> DatabaseStatsResponse:
        missions = self._db.load_all_missions()
        audit = self._db.load_audit_log(limit=100000)
        bad_rows_file = self._data_dir / "bad_rows.jsonl"
        quarantined_rows = 0
        if bad_rows_file.exists():
            quarantined_rows = sum(
                1
                for line in bad_rows_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )

        return DatabaseStatsResponse(
            ok=True,
            generated_at=datetime.now(timezone.utc),
            mission_rows=len(missions),
            audit_rows=len(audit),
            quarantined_rows=quarantined_rows,
        )
