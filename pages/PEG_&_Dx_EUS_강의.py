import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta, timezone
import requests

# Set page to wide mode
st.set_page_config(page_title="EGD 강의", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()   

# Check if Firebase app has already been initialized
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
    firebase_admin.initialize_app(cred)

# Display Form Title
st.subheader("PEG와 진단 EUS 강의 모음")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("- 이 EGD 기타 강의 모음은 PEG와 진단 EUS 대한 강의 동영상 모음입니다.")
    st.write("- 왼쪽 sidebar에서 시청하고자 하는 강의를 선택한 후 오른쪽 화면에서 강의 첫 화면이 나타납니다.")
    st.write("- 강의 첫 화면이 나타나면 화면을 클릭해서 시청하세요")
    st.write("- 전체 화면을 보실 수 있습니다. 화면 왼쪽 아래 전체 화면 버튼 누르세요.")
    st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")
        
# Lectures 폴더 내 mp4 파일 리스트 가져오기  
def list_mp4_files(bucket_name, directory):
    bucket = storage.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=directory)
    file_names = []
    for blob in blobs:
        if blob.name.endswith(".mp4"):
            file_name = os.path.basename(blob.name)
            file_names.append(file_name)
    return file_names

# 동영상 플레이어를 렌더링할 컨테이너 생성
video_player_container = st.container()

# 동영상 플레이어를 렌더링할 플레이스홀더 생성
video_player_placeholder = st.empty()

# 왼쪽 사이드바에서 강의 선택
lectures = ["Default", "PEG", "EUS_basic", "EUS_SET", "EUS_case"]
selected_lecture = st.sidebar.radio("강의를 선택하세요", lectures, index=0)

# 로그 파일 생성
if selected_lecture:
    # 'Default'일 경우 로그 파일 생성하지 않음
    if selected_lecture != "Default":
        name = st.session_state.get('name', 'unknown')
        position = st.session_state.get('position', 'unknown')
        access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)

        # 로그 내용을 문자열로 생성
        log_entry = f"Position: {position}, Name: {name}, Access Date: {access_date}, Lecture: {selected_lecture}\n"

        # Firebase Storage에 로그 파일 업로드
        bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
        log_blob = bucket.blob(f'log_PEG_EUS/{position}/{name}/{selected_lecture}')  # 로그 파일 경로 설정
        log_blob.upload_from_string(log_entry, content_type='text/plain')  # 문자열로 업로드


# 선택된 강의와 같은 이름의 mp4 파일 찾기
directory_lectures = "Lectures/"
mp4_files = list_mp4_files('amcgi-bulletin.appspot.com', directory_lectures)

# 선택된 강의에 해당하는 mp4 파일 찾기
selected_mp4 = None
for file_name in mp4_files:
    if file_name.startswith(selected_lecture):
        selected_mp4 = file_name
        break

if selected_mp4:
    # Firebase Storage에서 선택된 mp4 파일의 URL 생성
    selected_mp4_path = directory_lectures + selected_mp4
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    blob = bucket.blob(selected_mp4_path)
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
    mp4_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
    
    # 동영상 플레이어 렌더링
    with video_player_placeholder.container():
        video_html = f'''
        <div style="display: flex; justify-content: center;">
            <video width="1000" height="800" controls controlsList="nodownload">
                <source src="{mp4_url}" type="video/mp4">
            </video>
        </div>
        <script>
        var video_player = document.querySelector("video");
        video_player.addEventListener('contextmenu', function(e) {{
            e.preventDefault();
        }});
        </script>
        '''
        st.markdown(video_html, unsafe_allow_html=True)
else:
    st.sidebar.warning(f"{selected_lecture}에 해당하는 강의 파일을 찾을 수 없습니다.")

st.sidebar.divider()

if st.sidebar.button("Logout"):
    # 로그아웃 시간과 duration 계산
    logout_time = datetime.now(timezone.utc)
    login_time = st.session_state.get('login_time')
    if login_time:
        if not login_time.tzinfo:
            login_time = login_time.replace(tzinfo=timezone.utc)
        duration = round((logout_time - login_time).total_seconds() / 60)
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
    
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")