from fastapi import APIRouter
from .operator_session import OperatorSession
from .session_store import SessionStore

router = APIRouter()
session_store = SessionStore()
current_session = None


@router.post("/session/start")
def start_session(operator_id: str):
    global current_session
    current_session = OperatorSession(operator_id=operator_id, session_id="session_001")
    return {"message": "Session started", "session_id": current_session.session_id}


@router.get("/session/state")
def get_session_state():
    if current_session:
        return current_session.end_session()
    return {"message": "No active session"}


@router.post("/session/end")
def end_session():
    global current_session
    if current_session:
        session_data = current_session.end_session()
        session_store.append_session(session_data)
        current_session = None
        return {"message": "Session ended", "session_data": session_data}
    return {"message": "No active session to end"}
