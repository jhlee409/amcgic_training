import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth
import os
from datetime import datetime

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
def initialize_firebase_apps():
    # 첫 번째 Firebase 앱 (기본 앱)
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
        default_app = firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["database_url"]
        }, name='default')

    # 두 번째 Firebase 앱
    if 'secondary' not in firebase_admin._apps:
        cred_secondary = credentials.Certificate({
            "type": "service_account",
            "project_id": st.secrets["project_id_secondary"],
            "private_key_id": st.secrets["private_key_id_secondary"],
            "private_key": st.secrets["private_key_secondary"].replace('\\n', '\n'),
            "client_email": st.secrets["client_email_secondary"],
            "client_id": st.secrets["client_id_secondary"],
            "auth_uri": st.secrets["auth_uri_secondary"],
            "token_uri": st.secrets["token_uri_secondary"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url_secondary"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url_secondary"],
            "universe_domain": st.secrets["universe_domain_secondary"]
        })
        secondary_app = firebase_admin.initialize_app(cred_secondary, {
            'databaseURL': st.secrets["database_url_secondary"]
        }, name='secondary')

# Firebase 앱 초기화 실행
initialize_firebase_apps()

# Firebase 데이터베이스 참조 가져오기 함수
def get_db(app_name='default'):
    return db.reference(app=firebase_admin.get_app(name=app_name))

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
        response = requests.post(request_ref, headers=headers, json={"email": email, "password": password, "returnSecureToken": True})
        response_data = response.json()

        if response.status_code == 200:
            user_id = response_data['localId']
            id_token = response_data['idToken']
            
            # 첫 번째 데이터베이스에 사용자 정보 저장
            default_db = get_db('default')
            user_ref = default_db.reference(f'users/{user_id}')
            user_ref.update({
                'email': email,
                'name': name,
                'position': position,
                'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # 두 번째 데이터베이스에 로그 저장
            secondary_db = get_db('secondary')
            log_ref = secondary_db.reference('login_logs')
            log_ref.push({
                'user_id': user_id,
                'name': name,
                'position': position,
                'login_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'login'
            })

            # 로그인 시간 저장
            login_time = datetime.now()
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['user_name'] = name
            st.session_state['user_position'] = position
            st.session_state['user_id'] = user_id
            st.session_state['login_time'] = login_time

            st.success(f"환영합니다, {name}님! ({position})")
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
        try:
            # 로그아웃 시간 기록 및 체류 시간 계산
            logout_time = datetime.now()
            login_time = st.session_state.get('login_time')
            
            if login_time:
                # 체류 시간 계산 (분 단위)
                duration = (logout_time - login_time).total_seconds() / 60
                
                # Firebase에 로그아웃 및 체류 시간 기록
                user_id = st.session_state['user_id']
                secondary_db = get_db('secondary')
                log_ref = secondary_db.reference('login_logs')
                log_ref.push({
                    'user_id': user_id,
                    'name': st.session_state['user_name'],
                    'position': st.session_state['user_position'],
                    'logout_time': logout_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_minutes': round(duration, 2),
                    'type': 'logout'
                })
                
                st.success(f"로그아웃 되었습니다. 체류 시간: {round(duration, 2)}분")
            
            st.session_state.clear()
            st.experimental_rerun()
        except Exception as e:
            st.error(f"로그아웃 중 오류가 발생했습니다: {str(e)}")
