import streamlit as st
from uuid import uuid4
import requests

BASE_URL = "http://localhost:8000"

def start_app():
    try:

        response = requests.get(url = f"{BASE_URL}/health")
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "running":
            st.success("AEP Application is running")
        else:
            st.warning("AEP Application is not ready")

    except requests.exceptions.ConnectionError:
        st.error("AEP backend is not running")

    except requests.exceptions.Timeout:
        st.error("AEP health check timed out")

    except Exception as e:
        st.error(f" Application initialization failed: {e}")
    
def payload_send(user_name,thread_id,question):
    try:
        response = requests.post(url = f"{BASE_URL}/chat", json = {"user_name" : user_name, "thread_id" : thread_id , "question":question})
        response.raise_for_status()
        return response.json()
    except Exception:
        st.error("Processing failed")
        return None


def interrupt(decision:str, thread_id:str, user_name:str):
    try:
        response = requests.post(url = f"{BASE_URL}/resume", json = {"decision":decision, "thread_id": thread_id, "user_name":user_name})
        response.raise_for_status()
        return response.json()
    except Exception:
        st.error("Error while responding to interrupt call")
        return None
    
st.set_page_config(page_title="Agentic Engineering Platform", layout="wide")


# --------------------------------------------------
# Initialize session state
# --------------------------------------------------

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = None


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:

    st.title("Agentic Engineering Platform")

    user_name = st.text_input("User name", value = st.session_state.user_name or "", placeholder="Enter user name")

    # ----------------------------------------------
    # Detect user change
    # ----------------------------------------------

    if user_name != st.session_state.user_name:

        st.session_state.user_name = user_name
        # New user -> new thread
        st.session_state.thread_id = str(uuid4())
        # Clear previous conversation
        st.session_state.messages = []
        st.session_state.pending_approval = None
        st.rerun()


    st.divider()

    st.write("Current Thread")

    if st.session_state.thread_id:
        st.code(st.session_state.thread_id)


    # ----------------------------------------------
    # New Chat
    # ----------------------------------------------

    if st.button(" + New Chat", use_container_width=True):
        st.session_state.thread_id = str(uuid4())
        st.session_state.messages = []
        st.session_state.pending_approval = None

        st.rerun()


# --------------------------------------------------
# Main page
# --------------------------------------------------
start_app()

st.title("Agentic Engineering Platform 🤖")

# --------------------------------------------------
# Display messages
# --------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        if message["role"] == "user":
            st.write(f"**{message['user_name']}**")
            st.write(message["user_content"])

        elif message["role"] == "assistant":
            final_answer = message.get("final_answer")
            if not final_answer:
                continue
            status = final_answer.get("status")
            summary = final_answer.get("summary")
            result = final_answer.get("result")
            errors = final_answer.get("errors")
            metadata = final_answer.get("metadata")

            # STATUS
            st.subheader("Status")
            st.write(status)

            # SUMMARY
            if summary:
                st.subheader("Summary")
                st.write(summary)

            # RESULT
            if result:
                st.subheader("Result")
                st.markdown(result)

            # ERRORS
            if errors:
                st.subheader("Errors")
                st.write(errors)

            # METADATA
            if metadata:
                st.subheader("Metadata")
                st.json(metadata)
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
            "user_content": user_message
        }
    )

    with st.chat_message("user"): 
        st.write(f"**{st.session_state.user_name}**") 
        st.write(user_message)

    assistant_dummy_response = ( f"AEP received your message using thread " 
                           f"{st.session_state.thread_id}. "
                           f"Processing your request. Wait Patiently" 
                           )

    with st.chat_message("assistant"):
        st.write(assistant_dummy_response)

    response = payload_send(st.session_state.user_name, st.session_state.thread_id, user_message)
    

    if response is None:
        st.stop()

    if response.get("status") == "waiting_for_approval":
        st.session_state.pending_approval = response
    else:
        final_answer = response.get("final_answer")

        if final_answer:

            # Save the complete final answer
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "final_answer": final_answer
                }
            )

        st.rerun()


if st.session_state.pending_approval is not None:
    
    response = st.session_state.pending_approval

    st.warning("Approval Required")

    action_request = response["action_requests"][0]

    st.write("Tool")
    st.write(action_request["name"])

    st.write("Arguments:")
    st.json(action_request["args"])

    col1,col2 = st.columns(2)

    with col1:
        if st.button("Approve", key="approve_tool"):

            response = interrupt("approve", st.session_state.thread_id,st.session_state.user_name)

            if response is None:
                st.stop()

            if response.get("status") == "waiting_for_approval":
                st.session_state.pending_approval = response

            else:
                st.session_state.pending_approval = None
                final_answer = response.get("final_answer")
                st.session_state.messages.append({"role": "assistant", "final_answer": final_answer})

            st.rerun()

    with col2:
        if st.button("Reject",key = "reject_tool"):
            response = interrupt("reject", st.session_state.thread_id,st.session_state.user_name)

            if response is None:
                st.stop()

            if response.get("status") == "waiting_for_approval":
                st.session_state.pending_approval = response
            
            else:
                st.session_state.pending_approval = None
                final_answer = response.get("final_answer")
                st.session_state.messages.append({"role": "assistant", "final_answer": final_answer})

            st.rerun()



 



   
                


        