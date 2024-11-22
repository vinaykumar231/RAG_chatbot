from .session_management import  send_message
from fastapi import FastAPI, Query, APIRouter

router = APIRouter()

@router.post("/send-message")
def handle_message(user_input: str, session_id: str = Query(None)):
    return send_message(user_input, session_id)

