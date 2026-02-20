from datetime import datetime
from typing import List

from pydantic import BaseModel


class BootstrapChecks(BaseModel):
    data_dir_exists: bool
    audit_log_exists: bool
    missions_log_exists: bool


class BootstrapStatusResponse(BaseModel):
    ok: bool
    service: str
    version: str
    environment: str
    generated_at: datetime
    checks: BootstrapChecks
    warnings: List[str]


class BootstrapManifestResponse(BaseModel):
    ok: bool
    service: str
    capabilities: List[str]
    generated_at: datetime
