from datetime import datetime

from pydantic import BaseModel


class OperatorAuthStatusResponse(BaseModel):
    ok: bool
    auth_mode: str
    key_configured: bool
    generated_at: datetime


class OperatorAuthVerifyRequest(BaseModel):
    operator_key: str


class OperatorAuthVerifyResponse(BaseModel):
    ok: bool
    authenticated: bool
    message: str
    generated_at: datetime
