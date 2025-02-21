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

# Firebase 초기화 (앱이 이미 초기화되지 않았다면)
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

# Display Form Title
st.subheader("EGD 실전 강의 모음")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("- 이 강의 모음은 진단 EGD 실전 강의 동영상 모음입니다.")
    st.write("- 왼쪽에서 시청하고자 하는 강의를 선택한 후 오른쪽 화면에서 강의 첫 화면이 나타나면 화면을 클릭해서 시청하세요.")
    st.write("- 전체 화면을 보실 수 있습니다. 화면 왼쪽 아래 전체 화면 버튼 누르세요.")
    st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")

# 강의 목록
lectures = [
    "Default", 
    "Description_Impression", 
    "Photo_Report", 
    "Complication_Sedation", 
    "Biopsy_NBI", 
    "Stomach_benign", 
    "Stomach_malignant", 
    "Duodenum", 
    "Lx_Phx_Esophagus", 
    "SET"
]

# 사이드바에서 강의 선택
selected_lecture = st.sidebar.selectbox("강의를 선택하세요", lectures, key='lecture_selector')

# 강의 선택이 변경되었을 때 상태 초기화
if st.session_state.get('previous_lecture') != selected_lecture:
    # 로그인 관련 정보만 유지
    temp_login_info = {
        'logged_in': st.session_state.get('logged_in', False),
        'name': st.session_state.get('name'),
        'position': st.session_state.get('position'),
        'login_time': st.session_state.get('login_time')
    }
    
    # 세션 상태 초기화
    st.session_state.clear()
    
    # 로그인 정보 복원
    for key, value in temp_login_info.items():
        st.session_state[key] = value
    
    # 새로운 선택 저장
    st.session_state['previous_lecture'] = selected_lecture
    st.session_state['show_main_video'] = False
    st.rerun()

# 2:3 비율의 두 컬럼 생성
left_col, right_col = st.columns([2, 3])

# Lectures 폴더 내 mp4/docx 파일 경로 설정
directory_lectures = "Lectures/"
bucket_name = 'amcgi-bulletin.appspot.com'
bucket = storage.bucket(bucket_name)
expiration_time = datetime.now(pytz.UTC) + timedelta(seconds=1600)

# 선택된 강의가 Default가 아닐 때에만 동작
if selected_lecture != "Default":
    try:
        # 파일명 구성
        prevideo_name = f"{selected_lecture}_prevideo.mp4"
        docx_name = f"{selected_lecture}.docx"
        main_video_name = f"{selected_lecture}.mp4"

        # Firebase 경로
        prevideo_path = directory_lectures + prevideo_name
        docx_path = directory_lectures + docx_name
        main_video_path = directory_lectures + main_video_name

        # Blob 가져오기 및 URL 생성
        prevideo_blob = bucket.blob(prevideo_path)
        docx_blob = bucket.blob(docx_path)
        if prevideo_blob.exists():
            st.session_state['prevideo_url'] = prevideo_blob.generate_signed_url(
                expiration=expiration_time,
                method='GET'
            )
        
        # docx 파일 읽기
        if docx_blob.exists():
            content = docx_blob.download_as_bytes()
            doc = docx.Document(io.BytesIO(content))
            st.session_state['instruction_text'] = '\n'.join([para.text for para in doc.paragraphs])
        
        # main video 경로 저장
        st.session_state['main_video_path'] = main_video_path

    except Exception as e:
        st.error(f"파일을 불러오는 중 오류가 발생했습니다: {str(e)}")

# 좌우 컨테이너에 콘텐츠 표시
left_col, right_col = st.columns([2, 3])

# 왼쪽 컨테이너에 prevideo와 설명 표시
with left_col:
    if 'prevideo_url' in st.session_state and st.session_state['prevideo_url']:
        video_html = f"""
            <div style="width: 500px; margin: auto;">
                <video style="width: 100%; height: auto;" controls src="{st.session_state['prevideo_url']}">
                    Your browser does not support the video element.
                </video>
            </div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    
    if 'instruction_text' in st.session_state:
        st.markdown(st.session_state['instruction_text'])

# 사이드바에 본강의 시청 버튼
if st.sidebar.button("본강의 시청"):
    # 본강의 보이도록 플래그 설정
    st.session_state['show_main_video'] = True

    # 로그 파일 생성 및 전송
    if selected_lecture != "Default":
        name = st.session_state.get('name', 'unknown')
        position = st.session_state.get('position', 'unknown')
        access_date = datetime.now(pytz.UTC).strftime("%Y-%m-%d")

        log_entry = f"Position: {position}, Name: {name}, Access Date: {access_date}, 실전강의: {selected_lecture}\n"

        log_blob = bucket.blob(
            f'log_Dx_EGD_실전_강의/{position}*{name}*{selected_lecture}'
        )
        log_blob.upload_from_string(log_entry, content_type='text/plain')
    
    # 화면 갱신
    st.rerun()

st.sidebar.divider()

# 로그아웃 버튼
if st.sidebar.button("Logout"):
    # 로그아웃 시간과 duration 계산
    logout_time = datetime.now(pytz.UTC)
    login_time = st.session_state.get('login_time')
    if login_time:
        # tz정보가 없으면 추가
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

    # 세션 스테이트 전체 초기화
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")
