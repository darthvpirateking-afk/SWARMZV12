from pydantic import BaseModel
from typing import Optional


class SovereignDecisionRequest(BaseModel):
    # Add fields as expected by the API routes. Minimal stub for now.
    decision: Optional[str] = None
    operator_id: Optional[str] = None
    payload: Optional[dict] = None
