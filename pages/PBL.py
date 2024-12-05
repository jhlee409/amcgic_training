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
            # ChatGPT API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",  # Use the API key from secrets
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-4o",  # Specify the model
                "messages": [{"role": "user", "content": user_input}]  # Only include messages
            }

            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()

            # Handle API response
            if response.status_code == 200:
                chat_response = response_data['choices'][0]['message']['content']
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
                st.error("Error calling API: " + response_data.get("error", {}).get("message", "Unknown error"))
        else:
            st.error("Please enter a message.")
