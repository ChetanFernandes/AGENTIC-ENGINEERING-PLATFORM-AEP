import streamlit as st
from uuid import uuid4
import requests


BASE_URL = "http://localhost:8000"

#------------------service layer------------------------

def payload_send(user_name,thread_id,question):
    try:
        response = requests.post(url = f"{BASE_URL}/chat", json = {"user_name" : user_name, "thread_id" : thread_id , "question":question},timeout=300)
        response.raise_for_status()
        return response.json()
    except Exception:
        st.error("Processing failed")


st.set_page_config(
    page_title="Agentic Engineering Platform",
    layout="wide"
)


# --------------------------------------------------
# Initialize session state
# --------------------------------------------------

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.title("Agentic Engineering Platform")

    user_name = st.text_input("User name", value=st.session_state.user_name or "", placeholder="Enter user name")

    # ----------------------------------------------
    # Detect user change
    # ----------------------------------------------

    if user_name != st.session_state.user_name:

        st.session_state.user_name = user_name

        # New user -> new thread
        st.session_state.thread_id = str(uuid4())

        # Clear previous conversation
        st.session_state.messages = []

        st.rerun()


    st.divider()

    st.write("Current Thread")

    if st.session_state.thread_id:
        st.code(st.session_state.thread_id)


    # ----------------------------------------------
    # New Chat
    # ----------------------------------------------

    if st.button("＋ New Chat", use_container_width=True):

        st.session_state.thread_id = str(uuid4())

        st.session_state.messages = []

        st.rerun()


# --------------------------------------------------
# Main page
# --------------------------------------------------

st.title("Agentic Engineering Platform 🤖")


# --------------------------------------------------
# Display messages
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":
            st.write(f"**{message['user_name']}**")

        st.write(message["content"])


# --------------------------------------------------
# Chat input
# --------------------------------------------------

user_message = st.chat_input("Ask your AEP something...")


# --------------------------------------------------
# Process message
# --------------------------------------------------

if user_message:

    if not st.session_state.user_name:
        st.warning("Please enter your user name first.")
        st.stop()

    # Store user message
    st.session_state.messages.append(
        {
            "role": "user",
            "user_name": st.session_state.user_name,
            "content": user_message
        }
    )

    response = payload_send(st.session_state.user_name,st.session_state.thread_id,user_message)

    # Display user message
    with st.chat_message("user"):
        st.write(f"**{st.session_state.user_name}**")
        st.write(user_message)

    # Temporary response
    assistant_response = (
        f"I received your message using thread "
        f"`{st.session_state.thread_id}`"
    )

    # Store assistant message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_response
        }
    )

    # Display assistant response
    with st.chat_message("assistant"):
        st.write(assistant_response)