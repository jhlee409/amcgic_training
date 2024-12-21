import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth
import os
from supabase import create_client, Client
import time
import threading
from datetime import datetime, timezone, timedelta

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
if not firebase_admin._apps:

    # Streamlit Secrets에서 Firebase 설정 정보 로드
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

# Supabase 초기화
supabase: Client = create_client(
    st.secrets["supabase_url"],
    st.secrets["supabase_key"]
)

# 전역 변수 설정
user_data = {
    'user_name': None,
    'user_position': None,
    'is_logged_in': False
}

def update_login_info():
    while user_data['is_logged_in']:
        try:
            # 현재 시간을 KST로 설정
            current_time = "2024-12-21T23:19:45+09:00"
            
            # Supabase에 로그인 정보 저장
            data = {
                'user_name': user_data['user_name'],
                'user_position': user_data['user_position'],
                'time': current_time
            }
            supabase.table('login').insert(data).execute()
            
            # 1분 대기
            time.sleep(60)
        except Exception as e:
            st.error(f"로그인 정보 저장 중 오류 발생: {str(e)}")
            break

st.set_page_config(page_title="GI_training")

# 제목 및 서브헤딩 설정
st.title("GI training programs")

# 설명 텍스트
with st.expander("**이 프로그램 사용 방법**"):
    st.write("* 로그인이 제대로 안되면 왼쪽 증례 페이지에 접근할 수 없습니다.")
    st.write("* 등록된  이메일 주소와 PW, 한글이름, postion으로 로그인 하신 후 왼쪽 sidebar에서 원하는 프로그램을 선택하면 그 페이지로 이동합니다.")
    st.write("* 이 프로그램은 울산의대 서울아산병원 이진혁과 의대 관계자 및 여러 서울아산병원 소화기 선생님들의 참여에 의해 제작되었습니다.")
st.divider()

# 한글 이름 확인 함수
def is_korean_name(name):
    return any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in name)

# 사용자 인풋
email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")  # 이름 입력 필드 추가
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student"])  # 직책 선택 필드 추가

# 유효성 검사 및 로그인 버튼
login_disabled = False
if position == "":
    st.error("position을 선택해 주세요")
    login_disabled = True
if not name:
    st.error("한글 이름을 입력해 주세요")
    login_disabled = True
elif not name or not is_korean_name(name):
    st.error("한글 이름을 입력해 주세요")
    login_disabled = True

def handle_login(email, password, name, position):
    try:
        # Streamlit secret에서 Firebase API 키 가져오기
        api_key = st.secrets["FIREBASE_API_KEY"]
        request_ref = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})

        response = requests.post(request_ref, headers=headers, data=data)
        response_data = response.json()

        if response.status_code == 200:
            # Firebase Authentication 성공 후 사용자 정보 가져오기
            user_id = response_data['localId']
            id_token = response_data['idToken']  # ID 토큰 저장
            
            # Authentication 사용자 정보 업데이트
            try:
                user = auth.update_user(
                    user_id,
                    display_name=name,
                    custom_claims={'position': position}
                )
            except auth.UserNotFoundError:
                # 사용자가 없는 경우, 새로운 사용자 생성
                try:
                    user = auth.create_user(
                        uid=user_id,
                        email=email,
                        password=password,
                        display_name=name
                    )
                    # 생성된 사용자에 대한 custom claims 설정
                    auth.set_custom_user_claims(user_id, {'position': position})
                    st.success("새로운 사용자가 생성되었습니다.")
                except Exception as e:
                    st.error(f"사용자 생성 중 오류 발생: {str(e)}")
                    return
            
            # Realtime Database에도 정보 저장
            user_ref = db.reference(f'users/{user_id}')
            user_data = user_ref.get()

            if user_data is None:
                # 새 사용자인 경우 정보 저장
                user_ref.set({
                    'email': email,
                    'name': name,
                    'position': position,
                    'created_at': {'.sv': 'timestamp'}  # 서버 타임스탬프 사용
                })
                user_data = {'name': name, 'position': position}
            
            # position이 없는 경우 업데이트
            elif 'position' not in user_data:
                user_ref.update({
                    'position': position
                })
                user_data['position'] = position
            
            # 로그인 성공 시 전역 변수 업데이트
            user_data['user_name'] = name
            user_data['user_position'] = position
            user_data['is_logged_in'] = True
            
            # 백그라운드에서 로그인 정보 업데이트 시작
            update_thread = threading.Thread(target=update_login_info, daemon=True)
            update_thread.start()
            
            st.success("로그인 성공!")
            st.session_state['authenticated'] = True
            st.session_state['user_name'] = name
            st.session_state['user_position'] = position
            st.rerun()
            
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error(f"로그인 중 오류 발생: {str(e)}")

if st.button("Login", disabled=login_disabled):
    handle_login(email, password, name, position)

# 로그 아웃 버튼
if 'authenticated' in st.session_state and st.session_state['authenticated']:
    
    # 로그인된 사용자 정보 표시
    st.sidebar.write(f"**사용자**: {st.session_state.get('user_name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('user_position', '직책 미지정')}")
    
    if st.sidebar.button("Logout"):
        # 로그아웃 시 전역 변수 초기화
        user_data['is_logged_in'] = False
        user_data['user_name'] = None
        user_data['user_position'] = None
        
        st.session_state['authenticated'] = False
        st.session_state['user_name'] = None
        st.session_state['user_position'] = None
        st.success("로그아웃 되었습니다.")
        st.rerun()

user_email = st.session_state.get('user_email', 'unknown')  # 세션에서 이메일 가져오기