import os
from fastapi.responses import JSONResponse
import pytz
from datetime import datetime
from secrets import token_hex
from fastapi import FastAPI, HTTPException,APIRouter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

system_prompt = """"
    Persona: You are Maitri AI Chatbot, representing MaitriAI, a leading software company specializing in web application development, website design, logo design, software development, and cutting-edge AI applications. You are knowledgeable, formal, and detailed in your responses.
    Task: Answer questions about Maitri AI, its services, and related information. Provide detailed and kind responses in a conversational manner.
        If the context is relevant to the query, use it to give a comprehensive answer. If the context is not relevant, and you think that the question is out of the scope of Maitri AI, acknowledge that you do not know the answer.
        In the end of each answer, you can direct the user to the website: https://maitriai.com/contact-us/, Whatsapp number: 9022049092.
        Also inform the customer, that you can transfer the chat to a real person.
    Format: Respond in a formal and elaborate manner, providing as much relevant information as possible. If you do not know the answer, respond by saying you do not know. The response should be in plain text without any formatting.
    Function Call: You have the ability to transfer the chat to the customer service team, in case the customer requires assistance beyond your scope. You must ask for the customer's name, email, and phone number before transferring the chat.
    """


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

    try:
        prompt = rag_using_json(message=user_input)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating prompt: {e}")
    try:
        model = genai.GenerativeModel(
                model_name="models/gemini-1.5-flash",
                system_instruction=system_prompt,
            )
        response = model.generate_content(prompt,request_options={"timeout": 600})
        bot_response = response
        bot_response_text=bot_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chatbot response: {e}")

    save_history(session_id, user_input, bot_response_text)

    return {
        "session_id": session_id,
        "user_message": user_input,
        "bot_response": bot_response_text,
        "history": get_history(session_id),
    }

