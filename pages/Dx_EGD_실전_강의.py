import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage, db
from datetime import datetime, timedelta
import json

# Set page to wide mode
st.set_page_config(page_title="EGD 강의", layout="wide")

if st.session_state.get('logged_in'):

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
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
        })

    # Display Form Title
    st.subheader("EGD 실전 강의 모음")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 이 강의 모음은 진단 EGD 실전 강의 동영상 모음입니다.")
        st.write("- 왼쪽에서 시청하고자 하는 강의를 선택한 후 오른쪽 화면에서 강의 첫 화면이 나타나면 화면을 클릭해서 시청하세요.")
        st.write("- 전체 화면을 보실 수 있습니다. 화면 왼쪽 아래 전체 화면 버튼 누르세요.")

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
        # 'Default'일 경우 로그 파일 생성하지 않음
        if selected_lecture != "Default":
            try:
                user_name = st.session_state.get('user_name', 'unknown')
                user_position = st.session_state.get('user_position', 'unknown')
                position_name = f"{user_position}*{user_name}"
                access_date = datetime.now().strftime("%Y-%m-%d")
                
                log_entry = f"{position_name}*{access_date}*{selected_lecture}\n"
                
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                log_blob = bucket.blob(f'log_EGD_Dx_실전_강의/{position_name}*{selected_lecture}*{access_date}')
                log_blob.upload_from_string(log_entry, content_type='text/plain')
                st.success(f"강의 '{selected_lecture}'의 로그가 기록되었습니다.")
            except Exception as e:
                st.error(f"로그 기록 중 오류가 발생했습니다: {str(e)}")

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
        expiration_time = datetime.utcnow() + timedelta(seconds=1600)
        mp4_url = blob.generate_signed_url(expiration=expiration_time, method='GET')

        # 동영상 플레이어 렌더링
        with video_player_placeholder.container():
            # JavaScript에서 전송한 데이터를 처리할 콜백 함수
            def handle_watch_time(time, lecture):
                user_name = st.session_state.get('user_name', 'unknown')
                user_position = st.session_state.get('user_position', 'unknown')
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                # Firebase Realtime Database에 데이터 저장
                watch_ref = db.reference(f'watch_time/{user_position}/{user_name}')
                watch_ref.push({
                    'lecture': lecture,
                    'minutes_watched': time,
                    'date': current_date
                })

            video_html = f'''
            <div style="display: flex; justify-content: center;">
                <video id="video_player" width="1000" height="800" controls controlsList="nodownload">
                    <source src="{mp4_url}" type="video/mp4">
                </video>
            </div>
            <script>
                const video = document.getElementById('video_player');
                let lastReportedTime = 0;
                
                video.addEventListener('timeupdate', () => {{
                    const currentMinutes = Math.floor(video.currentTime / 60);
                    if (currentMinutes > lastReportedTime) {{
                        lastReportedTime = currentMinutes;
                        // Streamlit으로 데이터 전송
                        window.parent.Streamlit.setComponentValue({{
                            type: 'watchTime',
                            time: currentMinutes,
                            lecture: '{selected_lecture}'
                        }});
                    }}
                }});
                
                video.addEventListener('contextmenu', (e) => {{
                    e.preventDefault();
                }});
            </script>
            '''
            components = st.components.v1.html(video_html, height=850)
            
            # Streamlit 컴포넌트의 값이 변경될 때마다 호출
            if components:
                data = components
                if isinstance(data, dict) and data.get('type') == 'watchTime':
                    handle_watch_time(data['time'], data['lecture'])
    else:
        st.sidebar.warning(f"{selected_lecture}에 해당하는 강의 파일을 찾을 수 없습니다.")

    st.sidebar.divider()

    if st.sidebar.button('로그아웃'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

else:
    st.error("로그인이 필요합니다.")
