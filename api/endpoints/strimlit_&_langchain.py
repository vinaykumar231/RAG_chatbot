import os
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("API_KEY_gm")
genai.configure(api_key=api_key)

# Session management
class SessionManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "history": [],
            "created_at": datetime.now()
        }
        return session_id
    
    def save_history(self, session_id, user_message, bot_response):
        if session_id in self.sessions:
            self.sessions[session_id]["history"].append(f"User: {user_message}")
            self.sessions[session_id]["history"].append(f"Bot: {bot_response}")
    
    def get_history(self, session_id):
        return self.sessions.get(session_id, {}).get("history", [])
    
    def cleanup_sessions(self):
        current_time = datetime.now()
        self.sessions = {
            sid: details for sid, details in self.sessions.items() 
            if current_time - details["created_at"] <= timedelta(days=2)
        }

# Chatbot configuration
class MaitriAIChatbot:
    def __init__(self):
        # System prompt for the chatbot
        self.system_prompt = """
        Persona: You are Maitri AI Chatbot, representing MaitriAI, a leading software company specializing in web application development, website design, logo design, software development, and cutting-edge AI applications. You are knowledgeable, formal, and detailed in your responses.
        Task: Answer questions about Maitri AI, its services, and related information. Provide detailed and kind responses in a conversational manner.
        Additional Context: If the question is outside Maitri AI's scope, kindly inform the user and suggest contacting customer service.
        Closing: Always end your response by mentioning the contact details: 
        - Website: https://maitriai.com/contact-us/
        - WhatsApp: 9022049092
        """
        
        # Initialize session manager
        self.session_manager = SessionManager()
        
        # Initialize LangChain components
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        except Exception as e:
            st.error(f"Error initializing Google AI: {e}")
            self.llm = None
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template("{question}")
        ])
        
        # Create chain
        if self.llm:
            self.chain = (
                {"question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        else:
            self.chain = None
    
    def generate_response(self, user_input, session_id=None):
        # Create session if not provided
        if not session_id:
            session_id = self.session_manager.create_session()
        
        try:
            # Check if LLM and chain are initialized
            if not self.chain:
                return "AI service is currently unavailable. Please try again later.", session_id
            
            # Generate response
            bot_response = self.chain.invoke(user_input)
            
            # Save history
            self.session_manager.save_history(session_id, user_input, bot_response)
            
            return bot_response, session_id
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            st.error(error_message)
            return error_message, session_id

# Streamlit App
def main():
    st.set_page_config(page_title="Maitri AI Chatbot", page_icon="🤖")
    
    st.title("🤖 Maitri AI Chatbot")
    st.subheader("Your AI Assistant for Software and Web Solutions")
    
    # Initialize chatbot
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = MaitriAIChatbot()
    
    # Initialize session ID
    if 'session_id' not in st.session_state:
        st.session_state.session_id = st.session_state.chatbot.session_manager.create_session()
    
    # Chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to know about Maitri AI?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            response, session_id = st.session_state.chatbot.generate_response(
                prompt, 
                st.session_state.session_id
            )
            st.markdown(response)
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Update session ID (if changed)
        st.session_state.session_id = session_id

    # Additional information
    st.sidebar.title("Contact Information")
    st.sidebar.info("""
    🌐 Website: https://maitriai.com/contact-us/
    📱 WhatsApp: 9022049092
    
    Need personalized assistance? We're here to help!
    """)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2024 Maitri AI. All rights reserved.")

if __name__ == "__main__":
    main()