from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CompanionCoreStatusResponse(BaseModel):
    ok: bool
    source: str
    memory_version: int
    outcomes_count: int
    summary: str
    generated_at: datetime


class CompanionCoreMessageRequest(BaseModel):
    text: str
    operator_id: Optional[str] = None


class CompanionCoreMessageResponse(BaseModel):
    ok: bool
    reply: str
    source: str
    generated_at: datetime
