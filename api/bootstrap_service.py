import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from api.bootstrap_models import (
    BootstrapChecks,
    BootstrapManifestResponse,
    BootstrapStatusResponse,
)


class BootstrapService:
    def __init__(self, data_dir: str = "data") -> None:
        self._data_dir = Path(data_dir)

    def get_status(self) -> BootstrapStatusResponse:
        warnings: List[str] = []
        data_dir_exists = self._data_dir.exists()
        audit_log_exists = (self._data_dir / "audit.jsonl").exists()
        missions_log_exists = (self._data_dir / "missions.jsonl").exists()

        if not data_dir_exists:
            warnings.append("data directory is missing")
        if not audit_log_exists:
            warnings.append("audit log not initialized")
        if not missions_log_exists:
            warnings.append("missions log not initialized")

        return BootstrapStatusResponse(
            ok=True,
            service="swarmz",
            version=os.getenv("SWARMZ_VERSION", "0.1.0"),
            environment=os.getenv("SWARMZ_ENV", "development"),
            generated_at=datetime.now(timezone.utc),
            checks=BootstrapChecks(
                data_dir_exists=data_dir_exists,
                audit_log_exists=audit_log_exists,
                missions_log_exists=missions_log_exists,
            ),
            warnings=warnings,
        )

    def get_manifest(self) -> BootstrapManifestResponse:
        return BootstrapManifestResponse(
            ok=True,
            service="swarmz",
            capabilities=[
                "health",
                "missions",
                "companion",
                "build-dispatch",
                "bootstrap-status",
            ],
            generated_at=datetime.now(timezone.utc),
        )
