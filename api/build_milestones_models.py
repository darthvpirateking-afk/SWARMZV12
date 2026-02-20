from datetime import datetime
from typing import List

from pydantic import BaseModel


class BuildStageRecord(BaseModel):
    stage: int
    title: str
    status: str


class BuildStageExecutionRecord(BaseModel):
    stage: int
    title: str
    status: str
    executed_at: datetime


class BuildMilestonesStatusResponse(BaseModel):
    ok: bool
    current_stage: int
    target_stage: int
    total_stages: int
    stages: List[BuildStageRecord]
    history: List[BuildStageExecutionRecord]
    generated_at: datetime


class BuildMilestonesPromoteRequest(BaseModel):
    target_stage: int


class BuildMilestonesPromoteResponse(BaseModel):
    ok: bool
    current_stage: int
    target_stage: int
    applied_stages: List[BuildStageExecutionRecord]
    message: str
    generated_at: datetime
