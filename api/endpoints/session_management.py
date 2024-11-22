import os
from fastapi.responses import JSONResponse
import pytz
from datetime import datetime
from secrets import token_hex
from fastapi import FastAPI, HTTPException,APIRouter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


api_key = os.getenv("API_KEY_gm")

from api.endpoints.rag import rag_using_json

router=APIRouter
genai.configure(api_key=api_key)
sessions = {}


utc_now = pytz.utc.localize(datetime.utcnow())
ist_now = utc_now.astimezone(pytz.timezone('Asia/Kolkata'))

###################################  create sesion id ##########################################

def create_session_id(length: int = 16) -> str:
    random_token = token_hex(length)
    session_id = random_token
    sessions[session_id] = {
        "history": [],            
        "created_at": ist_now 
    }
    return session_id

################################### save history based on sesion id ##############################

def save_history(session_id, user_message, bot_response):
    if session_id in sessions:
        sessions[session_id]["history"].append(f"User: {user_message}")
        sessions[session_id]["history"].append(f"Bot: {bot_response}")
    else:
        print("Session ID not found!")

################################### get history based on sesion id #################################

def get_history(session_id):
    if session_id in sessions:
        return sessions[session_id]["history"]
    else:
        return "Session not found!"
    
################################### for clean session after 2 days ##################################
    
def cleanup_sessions():
    current_time = ist_now
    to_delete = []
    
    for session_id, details in sessions.items():
        if current_time - details["created_at"] > 172800:  # 2 days in seconds
            to_delete.append(session_id)
    
    for session_id in to_delete:
        del sessions[session_id]
        print(f"Deleted session: {session_id}")


def chatbot(query, session_id=None):
    if not session_id or session_id not in sessions:
        session_id = create_session_id()
        print(f"New session created: {session_id}")
    bot_response = f"I received your message: '{query}'"
    
    save_history(session_id, query, bot_response)
    
    return bot_response, session_id

def send_message(user_input: str, session_id: str = None):

    if not session_id or session_id not in sessions:
        session_id = create_session_id()
        print(f"New session created: {session_id}")

    try:
        prompt = rag_using_json(message=user_input)
        print("Prompt generated:", prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prompt: {e}")
    try:
        model = genai.GenerativeModel(
                model_name="models/gemini-1.5-flash",
                
            )
        
        response = model.generate_content(prompt, request_options={"timeout": 600})
        bot_response = f" '{response}'"  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chatbot response: {e}")

    save_history(session_id, user_input, bot_response)

    return {
        "session_id": session_id,
        "user_message": user_input,
        "bot_response": bot_response,
        "history": get_history(session_id),
    }

