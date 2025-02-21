import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta
import pytz
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
st.subheader("EGD 실전 강의 모음")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("- 이 강의 모음은 진단 EGD 실전 강의 동영상 모음입니다.")
    st.write("- 왼쪽에서 시청하고자 하는 강의를 선택한 후 오른쪽 화면에서 강의 첫 화면이 나타나면 화면을 클릭해서 시청하세요.")
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

# 2:3 비율의 두 컬럼 생성
left_col, right_col = st.columns([2, 3])

# 왼쪽 사이드바에서 강의 선택
lectures = ["Default", "Description_Impression", "Photo_Report", "Complication_Sedation", "Biopsy_NBI", "Stomach_benign", "Stomach_malignant", "Duodenum", "Lx_Phx_Esophagus", "SET"]

# 이전 선택값 확인을 위해 session_state에 저장된 값 가져오기
previous_lecture = st.session_state.get('previous_lecture', 'Default')
selected_lecture = st.sidebar.radio("강의를 선택하세요", lectures, index=0)

# 선택된 강의가 변경되었을 때
if selected_lecture != previous_lecture:
    st.session_state.prevideo_url = None
    st.session_state.main_video_url = None
    # show_main_video 상태 초기화
    st.session_state.show_main_video = False
    # 현재 선택을 저장
    st.session_state.previous_lecture = selected_lecture
    # 페이지 리프레시
    st.rerun()

# 선택된 강의와 같은 이름의 파일들 찾기
if selected_lecture != "Default":
    directory_lectures = "Lectures/"
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    expiration_time = datetime.now(pytz.UTC) + timedelta(seconds=1600)

    # prevideo 파일 경로
    prevideo_name = f"{selected_lecture}_prevideo.mp4"
    prevideo_path = directory_lectures + prevideo_name
    prevideo_blob = bucket.blob(prevideo_path)

    # docx 파일 경로
    docx_name = f"{selected_lecture}.docx"
    docx_path = directory_lectures + docx_name
    docx_blob = bucket.blob(docx_path)

    # 메인 비디오 파일 경로
    main_video_name = f"{selected_lecture}.mp4"
    main_video_path = directory_lectures + main_video_name
    main_video_blob = bucket.blob(main_video_path)

    # 왼쪽 컬럼에 prevideo와 docx 내용 표시
    with left_col:
        if prevideo_blob.exists():
            prevideo_url = prevideo_blob.generate_signed_url(expiration=expiration_time, method='GET')
            video_html = f'''
            <div style="display: flex; justify-content: center;">
                <video width="500px" controls controlsList="nodownload">
                    <source src="{prevideo_url}" type="video/mp4">
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

        if docx_blob.exists():
            # docx 파일 읽기
            docx_content = docx_blob.download_as_bytes()
            doc = docx.Document(io.BytesIO(docx_content))
            text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            st.write(text_content)

    # 오른쪽 컬럼은 본강의 재생을 위해 비워둠
    with right_col:
        if "show_main_video" in st.session_state and st.session_state.show_main_video:
            if main_video_blob.exists():
                main_video_url = main_video_blob.generate_signed_url(expiration=expiration_time, method='GET')
                video_html = f'''
                <div style="display: flex; justify-content: center;">
                    <video width="1300px" controls controlsList="nodownload">
                        <source src="{main_video_url}" type="video/mp4">
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

# 사이드바에 본강의 시청 버튼 추가
if st.sidebar.button("본강의 시청"):
    st.session_state.show_main_video = True
    
    # 로그 파일 생성 및 전송
    if selected_lecture != "Default":
        name = st.session_state.get('name', 'unknown')
        position = st.session_state.get('position', 'unknown')
        access_date = datetime.now(pytz.UTC).strftime("%Y-%m-%d")

        log_entry = f"Position: {position}, Name: {name}, Access Date: {access_date}, 실전강의: {selected_lecture}\n"

        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        log_blob = bucket.blob(f'log_Dx_EGD_실전_강의/{position}*{name}*{selected_lecture}')
        log_blob.upload_from_string(log_entry, content_type='text/plain')
    
    st.rerun()

st.sidebar.divider()

if st.sidebar.button("Logout"):
    # 로그아웃 시간과 duration 계산
    logout_time = datetime.now(pytz.UTC)
    login_time = st.session_state.get('login_time')
    if login_time:
        if not login_time.tzinfo:
            login_time = login_time.replace(tzinfo=pytz.UTC)
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