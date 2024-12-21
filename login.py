import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth, storage
import os
from datetime import datetime, timedelta
import threading

# Firebase 초기화
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
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'amcgi-bulletin.appspot.com',
        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
    })

st.set_page_config(page_title="GI Training")
st.title("GI Training Programs")

# Helper Functions
def save_log_to_storage(user_data, log_type):
    try:
        bucket = storage.bucket()
        current_time = datetime.now().strftime('%Y년%m월%d일-%H시%M분%S초')
        position_name = f"{user_data['position']}*{user_data['name']}"
        log_path = f'log_stay_duration/{position_name}*{current_time}_{log_type}'

        if log_type == '로그아웃':
            duration = user_data.get('duration', 0)
            log_content = f"{position_name}*{current_time}_{log_type}*{duration}분"
        else:
            log_content = f"{position_name}*{current_time}_{log_type}"

        blob = bucket.blob(log_path)
        blob.upload_from_string(log_content, content_type='text/plain')
        return True
    except Exception as e:
        st.error(f"로그 저장 중 오류 발생: {str(e)}")
        return False

# 자동 상태 저장 (1분마다)
def periodically_save_login_state():
    while st.session_state.get("logged_in", False):
        if "last_log_time" in st.session_state:
            last_log_time = st.session_state["last_log_time"]
            elapsed = (datetime.now() - last_log_time).total_seconds()
            if elapsed >= 60:  # 1분마다 로그 저장
                user_info = {
                    "name": st.session_state["user_name"],
                    "position": st.session_state["user_position"]
                }
                save_log_to_storage(user_info, "현재 로그인 상태")
                st.session_state["last_log_time"] = datetime.now()
        else:
            st.session_state["last_log_time"] = datetime.now()
        time.sleep(10)

# 로그인 처리
def handle_login(email, password, name, position):
    try:
        api_key = st.secrets["FIREBASE_API_KEY"]
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"email": email, "password": password, "returnSecureToken": True})
        )
        if response.status_code == 200:
            st.session_state.update({
                "logged_in": True,
                "user_email": email,
                "user_name": name,
                "user_position": position,
                "login_time": datetime.now()
            })
            save_log_to_storage({"name": name, "position": position}, "로그인")
            threading.Thread(target=periodically_save_login_state, daemon=True).start()
            st.success(f"환영합니다, {name}님! ({position})")
        else:
            st.error(response.json().get("error", {}).get("message", "로그인 실패"))
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {str(e)}")

# 로그아웃 처리
def handle_logout():
    try:
        if "login_time" in st.session_state:
            login_time = st.session_state["login_time"]
            duration = (datetime.now() - login_time).total_seconds() / 60
            duration = round(duration, 2)
            save_log_to_storage({
                "name": st.session_state["user_name"],
                "position": st.session_state["user_position"],
                "duration": duration
            }, "로그아웃")
            st.success(f"로그아웃 되었습니다. 체류 시간: {duration}분")
        st.session_state.clear()
        st.experimental_rerun()
    except Exception as e:
        st.error(f"로그아웃 중 오류 발생: {str(e)}")

# 로그인 UI
def main():
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    name = st.text_input("Name")
    position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student"])

    login_disabled = not email or not password or not name or not position
    if st.button("Login", disabled=login_disabled):
        handle_login(email, password, name, position)

    if st.session_state.get("logged_in", False):
        st.sidebar.write(f"**사용자**: {st.session_state["user_name"]}")
        st.sidebar.write(f"**직책**: {st.session_state["user_position"]}")
        if st.sidebar.button("Logout"):
            handle_logout()

if __name__ == "__main__":
    main()
