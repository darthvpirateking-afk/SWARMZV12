from pydantic import BaseModel
from typing import Optional

class IgnitionStateRequest(BaseModel):
    # Minimal stub fields; update as needed by the API route
    ignition_id: Optional[str] = None
    state: Optional[str] = None
