from fastapi import APIRouter
from .engine import PatchpackEngine

router = APIRouter()
engine = PatchpackEngine()


@router.post("/create")
def create_patch(payload: dict):
    return engine.create(payload)


@router.get("/list")
def list_patches():
    return engine.list()


@router.get("/load/{name}")
def load_patch(name: str):
    return engine.load(name)
