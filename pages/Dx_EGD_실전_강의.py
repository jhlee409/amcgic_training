import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta
import time
import threading

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
        firebase_admin.initialize_app(cred)

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
            user_name = st.session_state.get('user_name', 'unknown')
            user_position = st.session_state.get('user_position', 'unknown')
            position_name = f"{user_position}*{user_name}"  # 직책*이름 형식으로 저장
            access_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)

            # 로그 내용을 문자열로 생성
            log_entry = f"User: {position_name}, Access Date: {access_date}, 실전강의: {selected_lecture}\n"

            # Firebase Storage에 로그 파일 업로드
            bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
            log_blob = bucket.blob(f'log_Dx_EGD_실전_강의/{position_name}*{selected_lecture}')  # 로그 파일 경로 설정
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
        expiration_time = datetime.utcnow() + timedelta(seconds=1600)
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
    
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

    # 세션 상태에 last_log_time이 없으면 초기화
    if 'last_log_time' not in st.session_state:
        st.session_state['last_log_time'] = time.time()

    # 현재 시간과 마지막 로그 시간의 차이를 계산
    current_time = time.time()
    time_diff = current_time - st.session_state['last_log_time']

    # 1분(60초)이 지났으면 로그 저장
    if time_diff >= 60:
        def save_log_to_storage():
            try:
                if 'user_name' not in st.session_state or 'user_position' not in st.session_state:
                    print("사용자 정보가 세션에 없습니다.")
                    return
                    
                # Firebase Storage 버킷 가져오기
                bucket = storage.bucket()
                current_time = datetime.now().strftime('%Y년%m월%d일%H시%M분')
                position_name = f"{st.session_state['user_position']}*{st.session_state['user_name']}"
                
                # 로그 파일 경로 설정
                log_path = f'log_stay_duration/{position_name}*{current_time}'
                
                # 로그 내용 생성
                log_content = f"{position_name}*{current_time}"
                
                print(f"저장할 로그 경로: {log_path}")  # 디버깅용 출력
                print(f"저장할 로그 내용: {log_content}")  # 디버깅용 출력
                    
                # Firebase Storage에 로그 저장
                blob = bucket.blob(log_path)
                blob.upload_from_string(log_content, content_type='text/plain')
                
                print(f"로그 저장 성공: {current_time}")  # 디버깅용 출력
                return True
            except Exception as e:
                print(f"로그 저장 중 오류 발생: {str(e)}")  # 디버깅용 출력
                return False

        if save_log_to_storage():
            st.session_state['last_log_time'] = current_time
            print(f"로그 저장 시간 업데이트: {datetime.now().strftime('%Y년%m월%d일%H시%M분')}")

    # 자동 새로고침을 위한 빈 요소 (매 60초마다)
    st.empty()
    time.sleep(60)
    st.experimental_rerun()

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시 
    st.error("로그인이 필요합니다.")