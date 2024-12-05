import streamlit as st
import requests
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="PBL", layout="wide")

# Check if Firebase app has already been initialized
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"]
    })
    firebase_admin.initialize_app(cred)

# Streamlit sidebar for selecting PBL
st.sidebar.title("Menu")
selected_option = st.sidebar.radio("Select an option:", ["PBL"])

if selected_option == "PBL":
    st.title("PBL Chat")

    # User input for conversation
    user_input = st.text_input("Enter your message:")

    if st.button("Send"):
        if user_input:
            try:
                # Step 1: Create a new thread
                thread_url = "https://api.openai.com/v1/threads"  # Adjust the endpoint as necessary
                thread_headers = {
                    "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",  # Use the API key from secrets
                    "Content-Type": "application/json",
                    "OpenAI-Beta": "assistants=v2"  # Add the required header
                }
                thread_data = {
                    "assistant_id": "asst_TSbYs8y40TmTUqwEu9eGSF6w"  # Specify the assistant ID
                }

                thread_response = requests.post(thread_url, headers=thread_headers, data=json.dumps(thread_data))
                thread_response_data = thread_response.json()

                if thread_response.status_code == 200:
                    thread_id = thread_response_data['id']  # Get the new thread ID

                    # Step 2: Send a message to the new thread
                    message_url = "https://api.openai.com/v1/threads/messages"  # Adjust the endpoint as necessary
                    message_data = {
                        "thread_id": thread_id,
                        "role": "user",
                        "content": user_input
                    }

                    message_response = requests.post(message_url, headers=thread_headers, data=json.dumps(message_data))
                    message_response_data = message_response.json()

                    # Handle message response
                    if message_response.status_code == 200:
                        chat_response = message_response_data['choices'][0]['message']['content']
                        st.write("ChatGPT's response:", chat_response)

                        # Log user email and access date
                        user_email = st.session_state.get('user_email', 'unknown')
                        access_date = datetime.now().strftime("%Y-%m-%d")

                        # Log entry creation
                        log_entry = f"Email: {user_email}, Access Date: {access_date}, User Input: {user_input}, Response: {chat_response}\n"

                        # Upload log to Firebase Storage
                        bucket = storage.bucket('amcgi-bulletin.appspot.com')
                        log_blob = bucket.blob(f'logs/{user_email}_PBL_{access_date}.txt')
                        log_blob.upload_from_string(log_entry, content_type='text/plain')

                    else:
                        st.error("Error sending message: " + message_response_data.get("error", {}).get("message", "Unknown error"))
                else:
                    st.error("Error creating thread: " + thread_response_data.get("error", {}).get("message", "Unknown error"))

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")  # Handle any other exceptions
        else:
            st.error("Please enter a message.")
