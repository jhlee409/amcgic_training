import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth, storage
import os
from datetime import datetime
import time

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

st.set_page_config(page_title="GI_training")
st.title("GI Training Programs")

# 설명 텍스트
with st.expander("**이 프로그램 사용 방법**"):
    st.write("* 등록된 이메일, PW, 한글 이름, 직책으로 로그인.")
    st.write("* 왼쪽 사이드바에서 프로그램을 선택.")
st.divider()

# 한글 이름 확인 함수
def is_korean_name(name):
    return any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in name)

# 사용자 입력
email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student"])

# 로그인 버튼 활성화 조건
login_disabled = position == "" or not name or not is_korean_name(name)

# 로그 저장 함수
def save_log_to_storage(user_data, log_type):
    try:
        bucket = storage.bucket()
        current_time = datetime.now().strftime('%Y년%m월%d일-%H시%M분%S초')
        position_name = f"{user_data['position']}*{user_data['name']}"
        log_path = f'log_stay_duration/{position_name}*{current_time}_{log_type}'
        log_content = (
            f"{position_name}*{current_time}_{log_type}*{user_data.get('duration', 0)}분"
            if log_type == "로그아웃"
            else f"{position_name}*{current_time}_{log_type}"
        )
        blob = bucket.blob(log_path)
        blob.upload_from_string(log_content, content_type='text/plain')
        return True
    except Exception as e:
        st.error(f"로그 저장 중 오류 발생: {str(e)}")
        return False

# 1분마다 로그인 상태 저장
def periodically_save_login_state():
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        start_time = datetime.now()
        while st.session_state["logged_in"]:
            time.sleep(60)  # 60초 대기
            elapsed_time = (datetime.now() - start_time).total_seconds() / 60
            save_log_to_storage({
                "name": st.session_state["user_name"],
                "position": st.session_state["user_position"],
                "duration": round(elapsed_time, 2)
            }, "현재 로그인 상태")

# 로그인 처리 함수
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
            save_log_to_storage({"name": name, "position": position, "email": email}, "로그인")
            st.success(f"환영합니다, {name}님! ({position})")
            periodically_save_login_state()  # 자동 상태 저장 시작
        else:
            st.error(response.json().get("error", {}).get("message", "로그인 실패"))
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {str(e)}")

# 로그인 버튼
if st.button("Login", disabled=login_disabled):
    handle_login(email, password, name, position)

# 로그아웃 처리
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.sidebar.write(f"사용자: {st.session_state['user_name']}")
    st.sidebar.write(f"직책: {st.session_state['user_position']}")
    if st.sidebar.button("Logout"):
        logout_time = datetime.now()
        login_time = st.session_state.get("login_time")
        if login_time:
            duration = (logout_time - login_time).total_seconds() / 60
            save_log_to_storage({
                "name": st.session_state["user_name"],
                "position": st.session_state["user_position"],
                "duration": round(duration, 2)
            }, "로그아웃")
            st.success(f"로그아웃 되었습니다. 체류 시간: {round(duration, 2)}분")
        st.session_state.clear()
        st.experimental_rerun()