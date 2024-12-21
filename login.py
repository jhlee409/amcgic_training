import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth
import os
from datetime import datetime

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
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
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
    })

st.set_page_config(page_title="GI_training")

# 제목 및 서브헤딩 설정
st.title("GI training programs")

def is_korean_name(name):
    return any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in name)

email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student"])

login_disabled = False
if position == "":
    st.error("position을 선택해 주세요")
    login_disabled = True
if not name or not is_korean_name(name):
    st.error("한글 이름을 입력해 주세요")
    login_disabled = True

def handle_login(email, password, name, position):
    try:
        api_key = st.secrets["FIREBASE_API_KEY"]
        request_ref = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})

        response = requests.post(request_ref, headers=headers, data=data)
        response_data = response.json()

        if response.status_code == 200:
            user_id = response_data['localId']
            id_token = response_data['idToken']
            
            user_ref = db.reference(f'users/{user_id}')
            user_data = user_ref.get()

            if user_data is None:
                user_ref.set({
                    'email': email,
                    'name': name,
                    'position': position,
                    'created_at': {'.sv': 'timestamp'}
                })

            st.success(f"환영합니다, {name}님! ({position})")
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['user_name'] = name
            st.session_state['user_position'] = position
            st.session_state['user_id'] = user_id

            # 로그인 시간 저장
            st.session_state['login_time'] = datetime.now()
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if st.button("Login", disabled=login_disabled):
    handle_login(email, password, name, position)

if "logged_in" in st.session_state and st.session_state['logged_in']:
    st.sidebar.write(f"**사용자**: {st.session_state.get('user_name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('user_position', '직책 미지정')}")

    if st.sidebar.button("Logout"):
        # 로그아웃 시간 기록 및 체류 시간 계산
        logout_time = datetime.now()
        login_time = st.session_state.get('login_time', logout_time)
        duration = (logout_time - login_time).total_seconds() / 60  # 체류 시간(분)

        # Firebase에 기록 저장
        user_id = st.session_state['user_id']
        log_ref = db.reference(f'log_stay_duration/{user_id}')
        log_ref.push({
            'position': st.session_state['user_position'],
            'name': st.session_state['user_name'],
            'date': login_time.strftime('%Y%m%d%H%M'),
            'duration_minutes': duration
        })

        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.experimental_rerun()
