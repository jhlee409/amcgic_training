import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db, auth, storage
from datetime import datetime, timezone
import os
import tempfile

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

            # Supabase로 로그인 기록 추가
            supabase_url = st.secrets["supabase_url"]
            supabase_key = st.secrets["supabase_key"]
            supabase_headers = {
                "Content-Type": "application/json",
                "apikey": supabase_key,
                "Authorization": f"Bearer {supabase_key}"
            }

            login_time = datetime.now(timezone.utc)
            st.session_state['login_time'] = login_time.astimezone()  # Update login_time to be timezone-aware
            login_data = {
                "position": position,
                "name": name,
                "time": login_time.isoformat(),
                "event": "login",
                "duration": 0
            }

            supabase_response = requests.post(f"{supabase_url}/rest/v1/login", headers=supabase_headers, json=login_data)

            if supabase_response.status_code == 201:
                # Firebase Storage에서 기존 로그 폴더 삭제
                try:
                    bucket = storage.bucket()
                    
                    # log_login 폴더 삭제
                    login_blobs = list(bucket.list_blobs(prefix="log_login/"))
                    for blob in login_blobs:
                        try:
                            blob.delete()
                        except Exception as e:
                            st.error(f"로그인 로그 파일 삭제 중 오류 발생: {str(e)}")
                    
                    # log_logout 폴더 삭제
                    logout_blobs = list(bucket.list_blobs(prefix="log_logout/"))
                    for blob in logout_blobs:
                        try:
                            blob.delete()
                        except Exception as e:
                            st.error(f"로그아웃 로그 파일 삭제 중 오류 발생: {str(e)}")
                    
                    # 폴더 자체를 삭제하기 위한 빈 폴더 표시자 삭제
                    folder_markers = [
                        bucket.blob("log_login/"),
                        bucket.blob("log_logout/")
                    ]
                    for marker in folder_markers:
                        if marker.exists():
                            marker.delete()
                
                except Exception as e:
                    st.error(f"로그 폴더 삭제 중 오류 발생: {str(e)}")

                # 로그인 성공 시 로그 파일 생성 및 Firebase Storage에 업로드
                try:
                    # 현재 시간 가져오기 (초 단위까지)
                    now = datetime.now()
                    timestamp = now.strftime("%Y%m%d_%H%M%S")
                    
                    # 로그 파일 내용 생성
                    log_content = f"{position}*{name}*login*{now.strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # 임시 파일 생성
                    with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt') as temp_file:
                        temp_file.write(log_content)
                        temp_file_path = temp_file.name
                    
                    # Firebase Storage에 업로드
                    bucket = storage.bucket()
                    log_filename = f"log_login/{timestamp}"
                    blob = bucket.blob(log_filename)
                    blob.upload_from_filename(temp_file_path)
                    
                    # 임시 파일 삭제
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
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# 로그인 버튼
if st.button("Login", disabled=login_disabled):  # 원래 버튼 유지
    handle_login(email, password, name, position)

# 로그 아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    
    # 로그인된 사용자 정보 표시
    st.sidebar.write(f"**사용자**: {st.session_state.get('name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('position', '직책 미지정')}")
    
    if st.sidebar.button("Logout"):
        # 로그아웃 시간과 duration 계산
        logout_time = datetime.now(timezone.utc)
        login_time = st.session_state.get('login_time')
        if login_time:
            # 경과 시간을 분 단위로 계산하고 반올림
            duration = round((logout_time - login_time).total_seconds())
        else:
            duration = 0

        # 로그아웃 이벤트 기록
        logout_data = {
            "position": st.session_state.get('position'),
            "name": st.session_state.get('name'),
            "time": logout_time.isoformat(),
            "event": "logout",
            "duration": duration
        }
        
        # Supabase에 로그아웃 기록 전송
        supabase_url = st.secrets["supabase_url"]
        supabase_key = st.secrets["supabase_key"]
        supabase_headers = {
            "Content-Type": "application/json",
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        
        requests.post(f"{supabase_url}/rest/v1/login", headers=supabase_headers, json=logout_data)
        
        try:
            # 현재 시간 가져오기 (초 단위까지)
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")
            position = st.session_state.get('position', '')
            name = st.session_state.get('name', '')
            
            # Firebase Storage 버킷 가져오기
            bucket = storage.bucket()
            
            # 로그인 시간 가져오기
            login_timestamp = None
            login_blobs = list(bucket.list_blobs(prefix="log_login/"))
            
            # 현재 사용자의 가장 최근 로그인 찾기
            for blob in sorted(login_blobs, key=lambda x: x.name, reverse=True):
                try:
                    # 임시 파일에 다운로드
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        blob.download_to_filename(temp_file.name)
                        with open(temp_file.name, 'r') as f:
                            content = f.read()
                        os.unlink(temp_file.name)
                    
                    # 로그 내용 파싱
                    parts = content.split('*')
                    if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                        login_timestamp = datetime.strptime(parts[3], '%Y-%m-%d %H:%M:%S')
                        # 로그인 파일 찾았으므로 삭제
                        blob.delete()
                        break
                except Exception as e:
                    st.error(f"로그인 로그 파일 처리 중 오류 발생: {str(e)}")
            
            # 로그아웃 로그 파일 생성 및 업로드
            log_content = f"{position}*{name}*logout*{now.strftime('%Y-%m-%d %H:%M:%S')}"
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(log_content)
                temp_file_path = temp_file.name
            
            log_filename = f"log_logout/{timestamp}"
            blob = bucket.blob(log_filename)
            blob.upload_from_filename(temp_file_path)
            
            # 시간 차이 계산 및 duration 로그 생성
            if login_timestamp:
                time_diff_seconds = int((now - login_timestamp).total_seconds())
                duration_log_content = f"{position}*{name}*{time_diff_seconds}*{now.strftime('%Y-%m-%d %H:%M:%S')}"
                
                # duration 로그 파일 생성 및 업로드
                with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                    temp_file.write(duration_log_content)
                    duration_temp_path = temp_file.name
                
                duration_filename = f"log_duration/{position}*{name}*{time_diff_seconds}*{timestamp}"
                duration_blob = bucket.blob(duration_filename)
                duration_blob.upload_from_filename(duration_temp_path)
                os.unlink(duration_temp_path)
            
            # 로그아웃 로그 파일 삭제 (업로드 후)
            os.unlink(temp_file_path)
            
            # 모든 로그아웃 로그 파일 삭제
            logout_blobs = list(bucket.list_blobs(prefix="log_logout/"))
            for blob in logout_blobs:
                try:
                    # 현재 사용자의 로그아웃 파일만 삭제
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        blob.download_to_filename(temp_file.name)
                        with open(temp_file.name, 'r') as f:
                            content = f.read()
                        os.unlink(temp_file.name)
                    
                    parts = content.split('*')
                    if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                        blob.delete()
                except Exception as e:
                    st.error(f"로그아웃 로그 파일 삭제 중 오류 발생: {str(e)}")
            
        except Exception as e:
            st.error(f"로그 파일 처리 중 오류 발생: {str(e)}")
        
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
