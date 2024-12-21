import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta
from supabase import create_client

# Set page to wide mode
st.set_page_config(page_title="EGD 강의", layout="wide")

# Supabase 클라이언트 초기화
supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]
supabase_client = create_client(supabase_url, supabase_key)

if st.session_state.get('logged_in'):
    # Check if Firebase app has already been initialized
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

    # 시작 시간 기록
    start_time = datetime.now()

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
    lectures = ["Default", "Description_Impression", "Photo_Report", "Complication_Sedation", "Biopsy_NBI", "Stomach_benign", "Stomach_malignant", "Duodenum", "Lx_Phx_Esophagus", "SET"]
    selected_lecture = st.sidebar.radio("강의를 선택하세요", lectures, index=0)

    # 로그 파일 생성
    if selected_lecture:
        supabase_client.table("login_duration").insert({
            "user_position": "Manager",
            "user_name": "John Doe",
            "access_datetime": "2024-12-21 10:30:00",
            "duration": 15
        }).execute()
        
        if selected_lecture != "Default":
            user_name = st.session_state.get('user_name', 'unknown')
            user_position = st.session_state.get('user_position', 'unknown')
            position_name = f"{user_position}*{user_name}"  # 직책*이름 형식으로 저장
            access_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)

            log_entry = f"User: {position_name}, Access Date: {access_date}, 실전강의: {selected_lecture}\n"

            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            log_blob = bucket.blob(f'log_Dx_EGD_실전_강의/{position_name}*{selected_lecture}')
            log_blob.upload_from_string(log_entry, content_type='text/plain')

    # 선택된 강의와 같은 이름의 mp4 파일 찾기
    directory_lectures = "Lectures/"
    mp4_files = list_mp4_files('amcgi-bulletin.appspot.com', directory_lectures)

    selected_mp4 = None
    for file_name in mp4_files:
        if file_name.startswith(selected_lecture):
            selected_mp4 = file_name
            break

    if selected_mp4:
        selected_mp4_path = directory_lectures + selected_mp4
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        blob = bucket.blob(selected_mp4_path)
        expiration_time = datetime.utcnow() + timedelta(seconds=1600)
        mp4_url = blob.generate_signed_url(expiration=expiration_time, method='GET')

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

    if st.sidebar.button('로그아웃'):
        # 로그아웃 시 머무른 시간 계산 및 저장
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() // 60  # 분 단위로 계산

        user_name = st.session_state.get('user_name', 'unknown')
        user_position = st.session_state.get('user_position', 'unknown')
        access_datetime = start_time.strftime("%Y-%m-%d %H:%M")

        # Supabase에 데이터 저장
        supabase_client.table("login_duration").insert({
            "user_position": user_position,
            "user_name": user_name,
            "access_datetime": access_datetime,
            "duration": duration
        }).execute()

        st.session_state.logged_in = False
        st.rerun()
else:
    st.error("로그인이 필요합니다.")
