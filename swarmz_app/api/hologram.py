# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter
from swarmz_app.core.hologram_presence import get_hologram_payload

router = APIRouter(prefix="/v1/companion", tags=["Companion Hologram"])

@router.get("/hologram", response_model=dict)
def hologram():
    """
    Endpoint to retrieve the hologram JSON payload.
    Returns:
        dict: The full hologram JSON payload.
    """
    return get_hologram_payload()
