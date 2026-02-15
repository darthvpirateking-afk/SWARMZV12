"""{{PascalName}} router module."""

from fastapi import APIRouter

router = APIRouter(prefix="/{{kebabName}}", tags=["{{snakeName}}"])


@router.get("/")
async def list_{{snakeName}}():
    """List all {{snakeName}} items."""
    return []


@router.get("/{item_id}")
async def get_{{snakeName}}(item_id: int):
    """Get a single {{snakeName}} item by ID."""
    return {"id": item_id}


@router.post("/")
async def create_{{snakeName}}():
    """Create a new {{snakeName}} item."""
    return {"status": "created"}
