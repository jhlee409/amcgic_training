import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta

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

    # Firebase Storage에서 mp4 파일 리스트 가져오기
    def list_mp4_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        return [os.path.basename(blob.name) for blob in blobs if blob.name.endswith(".mp4")]

    # 동영상 플레이어를 렌더링할 플레이스홀더 생성
    video_player_placeholder = st.empty()

    # 왼쪽 사이드바에서 강의 선택
    lectures = ["Default", "Description_Impression", "Photo_Report", "Complication_Sedation", "Biopsy_NBI", "Stomach_benign", "Stomach_malignant", "Duodenum", "Lx_Phx_Esophagus", "SET"]
    selected_lecture = st.sidebar.radio("강의를 선택하세요", lectures, index=0)

    # 선택된 강의와 같은 이름의 mp4 파일 찾기
    directory_lectures = "Lectures/"
    mp4_files = list_mp4_files('amcgi-bulletin.appspot.com', directory_lectures)
    mp4_files.sort()  # 파일 이름 알파벳 순으로 정렬
    selected_mp4 = next((file for file in mp4_files if file.startswith(selected_lecture)), None)

    if selected_mp4:
        # Generate Firebase Signed URL
        selected_mp4_path = directory_lectures + selected_mp4
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        blob = bucket.blob(selected_mp4_path)
        expiration_time = datetime.utcnow() + timedelta(seconds=3600)
        mp4_url = blob.generate_signed_url(expiration=expiration_time, method='GET')

        # 세션 상태 초기화
        if 'log_sent' not in st.session_state:
            st.session_state.log_sent = set()

        # 동영상 플레이어 표시
        with video_player_placeholder.container():
            video_html = f'''
            <div style="display: flex; justify-content: center;">
                <video id="myVideo" width="1000" height="800" controls controlsList="nodownload">
                    <source src="{mp4_url}" type="video/mp4">
                </video>
                <div id="playTime" style="display: none;">0</div>
            </div>
            <script>
                var video = document.getElementById('myVideo');
                var playTime = document.getElementById('playTime');
                var totalPlayTime = 0;
                var isPlaying = false;
                var logSent = false;
                
                video.addEventListener('play', function() {{
                    isPlaying = true;
                    checkPlayTime();
                }});
                
                video.addEventListener('pause', function() {{
                    isPlaying = false;
                }});
                
                video.addEventListener('ended', function() {{
                    isPlaying = false;
                }});
                
                video.addEventListener('contextmenu', function(e) {{
                    e.preventDefault();
                }});
                
                function checkPlayTime() {{
                    if (isPlaying && !logSent) {{
                        totalPlayTime += 1;
                        playTime.textContent = totalPlayTime;
                        
                        if (totalPlayTime >= 180) {{  
                            logSent = true;
                            window.parent.postMessage({{
                                type: 'send_log',
                                lecture: '{selected_lecture}'
                            }}, '*');
                        }}
                        
                        setTimeout(checkPlayTime, 1000);
                    }}
                }}
            </script>
            '''
            st.components.v1.html(video_html, height=850)
            
            # JavaScript 메시지 수신을 위한 컴포넌트
            st.components.v1.html(
                """
                <script>
                    window.addEventListener('message', function(e) {
                        if (e.data.type === 'send_log') {
                            window.parent.postMessage(e.data, '*');
                        }
                    });
                </script>
                """,
                height=0
            )

        # JavaScript에서 메시지를 받아 로그 전송
        if selected_lecture not in st.session_state.log_sent:
            try:
                user_name = st.session_state.get('user_name', 'unknown')
                user_position = st.session_state.get('user_position', 'unknown')
                access_date = datetime.now().strftime("%Y-%m-%d")
                
                log_entry = f"사용자: {user_name}\n직급: {user_position}\n날짜: {access_date}\n실전강의: {selected_lecture}\n"
                
                log_blob = bucket.blob(f'log_Dx_EGD_실전_강의/{user_position}*{user_name}*{selected_lecture}')
                log_blob.upload_from_string(log_entry, content_type='text/plain')
                
                st.session_state.log_sent.add(selected_lecture)
                st.success(f"강의 '{selected_lecture}'의 로그가 기록되었습니다.")
            except Exception as e:
                st.error(f"로그 기록 중 오류가 발생했습니다: {str(e)}")

    else:
        st.sidebar.warning(f"{selected_lecture}에 해당하는 강의 파일을 찾을 수 없습니다.")

    # 로그아웃 버튼
    if st.sidebar.button('로그아웃'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

else:
    st.error("로그인이 필요합니다.")
