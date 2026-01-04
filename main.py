import streamlit as st
import pyrebase
import requests
import os
from dotenv import load_dotenv

# 1. MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="HuggingFace ChatBot", layout="centered")

load_dotenv()

# --- RESET BUTTON (Optional, moved below config) ---
if st.sidebar.button("RESET_SESSION"):
    st.session_state.clear()
    st.rerun()

# -------------------------
# Firebase Config
# -------------------------
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# -------------------------
# HuggingFace Config
# -------------------------
API_KEY = os.getenv("HUGGINGFACE_API_KEY")
API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "meta-llama/Llama-3.2-3B-Instruct"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def query_hf(message, chat_history=None):
    messages = []
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": message})

    payload = {"model": MODEL, "messages": messages, "max_tokens": 200}
    response = requests.post(API_URL, headers=headers, json=payload)

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return f"❌ Error: {response.text}"

# -------------------------
# Session State Initialization
# -------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "bot_history" not in st.session_state:
    st.session_state.bot_history = []

# -------------------------
# MAIN LOGIC
# -------------------------

if st.session_state.user is None:
    # --- LOGIN PAGE ---
    st.title("🔐 Login")
    email = st.text_input("Email:")
    password = st.text_input("Password:", type="password")

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = email
            st.success(f"Welcome {email}! 🎉")
            st.rerun() # Refresh to hide login and show chatbot
        except Exception as e:
            st.error("❌ Invalid email or password")
else:
    # --- CHATBOT PAGE ---
    st.title("🤖 HuggingFace ChatBot")
    st.sidebar.write(f"Logged in as: **{st.session_state.user}**")
    
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.chat_history = []
        st.session_state.bot_history = []
        st.rerun()

    user_msg = st.text_input("Type your message:", key="user_input")

    if st.button("Send"):
        if user_msg.strip() == "":
            st.warning("Please type something.")
        else:
            with st.spinner("Thinking..."):
                bot_reply = query_hf(user_msg, st.session_state.chat_history)

                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                st.session_state.bot_history.append((user_msg, bot_reply))

    # Display chat
    for u_msg, b_reply in reversed(st.session_state.bot_history):
        st.markdown(f"**You:** {u_msg}")
        st.markdown(f"**Bot:** {b_reply}")
        st.markdown("---")