from datetime import datetime
from typing import List

from pydantic import BaseModel


class DatabaseCollectionEntry(BaseModel):
    name: str
    path: str
    exists: bool
    size_bytes: int


class DatabaseStatusResponse(BaseModel):
    ok: bool
    engine: str
    data_dir: str
    generated_at: datetime


class DatabaseCollectionsResponse(BaseModel):
    ok: bool
    generated_at: datetime
    collections: List[DatabaseCollectionEntry]


class DatabaseStatsResponse(BaseModel):
    ok: bool
    generated_at: datetime
    mission_rows: int
    audit_rows: int
    quarantined_rows: int
