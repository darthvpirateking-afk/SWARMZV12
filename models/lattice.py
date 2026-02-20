from pydantic import BaseModel
from typing import Optional


class LatticeStatusRequest(BaseModel):
    # Minimal stub fields; update as needed by the API route
    lattice_id: Optional[str] = None
    status: Optional[str] = None
