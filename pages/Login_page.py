import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth, storage
from datetime import datetime, timezone
import os
import tempfile
import uuid
import socket

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
        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"],
        'storageBucket': 'amcgi-bulletin.appspot.com'
    })

st.set_page_config(page_title="amcgic_education")

# 제목 및 서브헤딩 설정.
st.title("AMC GI 상부 Education Program")
# 설명 텍스트
with st.expander("**이 프로그램 사용 방법**"):
    st.write("* 로그인이 제대로 안되면 왼쪽 증례 페이지에 접근할 수 없습니다.")
    st.write("* 등록된  이메일 주소와 PW, 한글이름, postion으로 로그인 하신 후 왼쪽 sidebar에서 원하는 프로그램을 선택하면 그 페이지로 이동합니다.")

# 한글 이름 확인 함수
def is_korean_name(name):
    return any('\u3131' <= char <= '\u3163' or '\uac00' <= char <= '\ud7a3' for char in name)

# 사용자 인풋
email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")  # 이름 입력 필드 추가
position = st.selectbox("Select Position", ["", "Staff", "F1", "F2", "R3", "Student", "신촌", "계명"])  # 직책 선택 필드 추가

# 로그인 버튼 클릭 전 초기화
login_disabled = True  # 초기값 설정

# 유효성 검사 및 로그인 버튼
if st.button("입력 확인"):  # 버튼 이름을 변경하여 ID 충돌 방지
    # 모든 조건이 충족되면 login_disabled를 False로 설정
    if (email != "" and 
        password != "" and 
        position != "" and 
        name != "" and 
        is_korean_name(name)):
        login_disabled = False
        st.success("입력이 확인되었습니다. 로그인 버튼을 클릭해주세요.")
    else:
        login_disabled = True
        if email == "":
            st.error("이메일을 입력해 주세요")
        if password == "":
            st.error("비밀번호를 입력해 주세요")
        if position == "":
            st.error("position을 선택해 주세요")
        if name == "":
            st.error("한글 이름을 입력해 주세요")
        elif not is_korean_name(name):
            st.error("한글 이름을 입력해 주세요")

# 세션 관리를 위한 유틸리티 함수들
def generate_session_id():
    return str(uuid.uuid4())

def get_client_ip():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except:
        return "unknown"

# Supabase 관련 함수 삭제됨

def handle_logout():
    try:
        user_id = st.session_state.get('user_id')
        position = st.session_state.get('position')
        name = st.session_state.get('name')
        
        if user_id:
            # 활성 세션 삭제
            user_session_ref = db.reference(f'users/{user_id}/activeSession')
            current_session = user_session_ref.get()
            
            if current_session:
                # 로그아웃 시간과 duration 계산
                logout_time = datetime.now(timezone.utc)
                login_time = datetime.fromtimestamp(current_session.get('loginTime') / 1000, tz=timezone.utc)
                duration = round((logout_time - login_time).total_seconds())
                # Supabase 기록 삭제됨
                # 세션 삭제
                user_session_ref.delete()

        # Firebase Storage 관련 작업
        try:
            now = datetime.now(timezone.utc)
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            # Firebase Storage 버킷 가져오기
            bucket = storage.bucket()
            # 로그아웃 로그 파일 생성 및 업로드
            log_content = f"{position}*{name}*logout*{now.strftime('%Y-%m-%d %H:%M:%S')}"
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(log_content)
                temp_file_path = temp_file.name
            log_filename = f"log_logout/{timestamp}"
            blob = bucket.blob(log_filename)
            blob.upload_from_filename(temp_file_path)
            os.unlink(temp_file_path)
        except Exception as e:
            st.error(f"로그 파일 처리 중 오류 발생: {str(e)}")
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
    except Exception as e:
        st.error(f"로그아웃 처리 중 오류 발생: {str(e)}")

def check_active_session():
    try:
        user_id = st.session_state.get('user_id')
        if user_id:
            user_session_ref = db.reference(f'users/{user_id}/activeSession')
            current_session = user_session_ref.get()
            
            if current_session:
                session_id = current_session.get('sessionId')
                if session_id != st.session_state.get('session_id'):
                    # 다른 세션에 의해 로그아웃됨
                    st.warning("다른 기기에서 로그인이 감지되어 로그아웃됩니다.")
                    handle_logout()
                    st.experimental_rerun()
    except Exception as e:
        st.error(f"세션 확인 중 오류 발생: {str(e)}")

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
            id_token = response_data['idToken']

            # 현재 활성 세션 확인
            user_session_ref = db.reference(f'users/{user_id}/activeSession')
            current_session = user_session_ref.get()
            
            if current_session:
                # 기존 세션이 있는 경우, 조용히 종료 처리 (로그아웃 메시지 없이)
                try:
                    # 로그아웃 시간과 duration 계산
                    logout_time = datetime.now(timezone.utc)
                    login_time = datetime.fromtimestamp(current_session.get('loginTime') / 1000, tz=timezone.utc)
                    duration = round((logout_time - login_time).total_seconds())
                    # Supabase 기록 삭제됨
                    # 세션 삭제
                    user_session_ref.delete()
                except Exception as e:
                    # 오류가 발생해도 사용자에게 표시하지 않음
                    pass
            # 새로운 세션 생성
            session_id = generate_session_id()
            new_session = {
                'sessionId': session_id,
                'ipAddress': get_client_ip(),
                'loginTime': {'.sv': 'timestamp'},
                'lastActive': {'.sv': 'timestamp'}
            }
            user_session_ref.set(new_session)
            # 세션 ID를 상태에 저장
            st.session_state['session_id'] = session_id
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
            # 로그인 성공 시 로그 파일 생성 및 Firebase Storage에 업로드
            try:
                now = datetime.now(timezone.utc)
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                log_content = f"{position}*{name}*login*{now.strftime('%Y-%m-%d %H:%M:%S')}"
                with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_file:
                    temp_file.write(log_content)
                    temp_file_path = temp_file.name
                bucket = storage.bucket()
                log_filename = f"log_login/{timestamp}"
                blob = bucket.blob(log_filename)
                blob.upload_from_filename(temp_file_path)
                os.unlink(temp_file_path)
                st.success(f"환영합니다, {user_data.get('name', email)}님! ({user_data.get('position', '직책 미지정')})")
            except Exception as e:
                st.error(f"로그 파일 업로드 중 오류 발생: {str(e)}")
                st.success(f"환영합니다, {user_data.get('name', email)}님! ({user_data.get('position', '직책 미지정')})")
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['name'] = name
            st.session_state['position'] = position
            st.session_state['user_id'] = user_id
            st.session_state['login_time'] = datetime.now(timezone.utc)
            # 로그인 성공 후 자동 새로고침하여 navigation 메뉴 업데이트
            st.rerun()
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# 로그인 버튼
if st.button("Login", disabled=login_disabled):  # 원래 버튼 유지
    handle_login(email, password, name, position)

# 로그인된 상태에서 세션 체크
if "logged_in" in st.session_state and st.session_state['logged_in']:
    check_active_session()

# 로그 아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    
    # 로그인된 사용자 정보 표시
    st.sidebar.write(f"**사용자**: {st.session_state.get('name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('position', '직책 미지정')}")
    
    if st.sidebar.button("Logout"):
        handle_logout()
