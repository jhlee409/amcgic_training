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
st.set_page_config(page_title="EGD_Hemostasis_lecture", layout="wide")

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
    st.subheader("EGD_Hemostasis_lecture")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 가장 먼저 왼쪽 sidebar 선택버튼에서 default는 'Default'입니다. Hemostasis lecture, cases 중 한 가지를 선택합니다.")
        st.write("- 우선 EGD 지혈술의 overview 강의를 시청하고 싶으면, Hemostasis lecture를 선택하고 '진행' 버튼을 누르면 강의 화면이 나타납니다. 클릭해서 시청하세요.")
        st.write("- EGD 지혈술 case를 시청하고 싶으면 cases 버튼을 선택하고 드롭다운 메뉴에서 case를 선택하면 치료전 case 동영상과 질문이 나타납니다.")
        st.write("- 잘 생각해 보고 '진행' 버튼을 누르면 답과 시술 동영상을 볼수있는 동영상 player가 나타납니다.")
        st.write("- 동영상을 클릭해서 보시면 됩니다.")
        st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")
          
    def list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        return [blob.name[len(directory):] for blob in blobs if blob.name[len(directory):]]
    
    def read_docx(bucket_name, file_name):
        try:
            bucket = storage.bucket(bucket_name)
            blob = bucket.blob(file_name)
            content = blob.download_as_bytes()
            doc = docx.Document(io.BytesIO(content))
            return '\n'.join([para.text for para in doc.paragraphs])
        except Exception as e:
            st.error(f"문서를 읽는 중 오류 발생: {str(e)}")
            return ""

    folder_selection = st.sidebar.radio("선택 버튼", ["Default", "Hemostasis lecture", "cases"])
    
    directories = {
        "Default": "EGD_Hemostasis_training/default/",
        "Hemostasis lecture": "EGD_Hemostasis_training/lecture/",
        "cases": "EGD_Hemostasis_training/cases/"
    }

    directory = directories[folder_selection]
    prevideo_dir, instruction_dir, video_dir = directory + "prevideos/", directory + "instructions/", directory + "videos/"
    
    # 폴더 선택이 변경되었을 때 상태 초기화
    if st.session_state.get('previous_folder_selection') != folder_selection:
        st.session_state.previous_folder_selection = folder_selection
        st.session_state.selected_prevideo_file = None
        st.session_state.prevideo_url = None
        # 현재 선택된 폴더의 파일 목록을 가져오기
        st.session_state.current_file_list = list_files('amcgi-bulletin.appspot.com', prevideo_dir)
        st.rerun()
    
    # 현재 폴더의 파일 목록 사용
    file_list_prevideo = st.session_state.get('current_file_list', list_files('amcgi-bulletin.appspot.com', prevideo_dir))
    selected_prevideo_file = st.sidebar.selectbox("파일 선택", file_list_prevideo)
    
    if selected_prevideo_file and selected_prevideo_file != st.session_state.get('selected_prevideo_file'):
        st.session_state.selected_prevideo_file = selected_prevideo_file
        prevideo_path = prevideo_dir + selected_prevideo_file
        instruction_file = instruction_dir + os.path.splitext(selected_prevideo_file)[0] + '.docx'
        
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        blob = bucket.blob(prevideo_path)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
        st.session_state.prevideo_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
        
        st.session_state.instruction_text = read_docx('amcgi-bulletin.appspot.com', instruction_file)
        
        video_name = os.path.splitext(selected_prevideo_file)[0] + '_main.mp4'
        st.session_state.selected_video_file = video_dir + video_name
        
        st.rerun()
    
    # 좌우 컨테이너 생성
    left_col, right_col = st.columns([2, 3])
    
    # 왼쪽 컨테이너에 첫 번째 동영상과 설명 표시
    with left_col:
        if st.session_state.get('prevideo_url'):
            video_html = f"""
                <div style="width: 600px; margin: auto;">
                    <video style="width: 100%; height: auto;" controls src="{st.session_state.prevideo_url}">
                        Your browser does not support the video element.
                    </video>
                </div>
            """
            st.markdown(video_html, unsafe_allow_html=True)
        if st.session_state.get('instruction_text'):
            st.markdown(st.session_state.instruction_text)
    
    # 오른쪽 컨테이너에 '진행' 버튼 클릭 시 나타나는 동영상 표시
    with right_col:
        if st.sidebar.button('진행'):
            user_name = st.session_state.get('user_name', 'unknown')
            user_position = st.session_state.get('user_position', 'unknown')
            access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            log_entry = f"사용자: {user_name}\n직급: {user_position}\n날짜: {access_date}\n메뉴: {os.path.splitext(selected_prevideo_file)[0]}\n"
            
            log_blob = storage.bucket('amcgi-bulletin.appspot.com').blob(f'log_EGD_Hemostasis/{user_position}*{user_name}*{os.path.splitext(selected_prevideo_file)[0]}')
            log_blob.upload_from_string(log_entry, content_type='text/plain')
            
            if st.session_state.get('selected_video_file'):
                blob = storage.bucket('amcgi-bulletin.appspot.com').blob(st.session_state.selected_video_file)
                expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
                video_url = blob.generate_signed_url(
                    expiration=expiration_time, 
                    method='GET',
                    response_disposition='attachment; filename="stream.m3u8"',
                    response_type='application/x-mpegURL'
                )
                
                video_html = f"""
                    <div style="width: 1000px; margin: auto;">
                        <style>
                            .video-container {{
                                position: relative;
                                width: 100%;
                                background: #000;
                            }}
                            video {{
                                width: 100%;
                                height: auto;
                                display: block;
                            }}
                            .video-shield {{
                                position: absolute;
                                top: 0;
                                left: 0;
                                width: 100%;
                                height: 100%;
                                background: transparent;
                                z-index: 2;
                            }}
                        </style>
                        <div class="video-container" id="videoContainer">
                            <video 
                                id="secureVideo"
                                controls 
                                controlsList="nodownload noplaybackrate nofullscreen"
                                disablePictureInPicture
                                webkit-playsinline 
                                playsinline
                                crossorigin="anonymous">
                            </video>
                            <div class="video-shield"></div>
                        </div>
                        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                        <script>
                            (function() {{
                                const video = document.getElementById('secureVideo');
                                const videoUrl = "{video_url}";
                                
                                // HLS 설정
                                if (Hls.isSupported()) {{
                                    const hls = new Hls({{
                                        debug: false,
                                        enableWorker: true,
                                        lowLatencyMode: true,
                                    }});
                                    
                                    hls.loadSource(videoUrl);
                                    hls.attachMedia(video);
                                    
                                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                                        video.play();
                                    }});
                                }}
                                
                                // 보안 설정
                                document.addEventListener('contextmenu', e => e.preventDefault(), true);
                                document.addEventListener('keydown', e => {{
                                    if (e.ctrlKey || e.metaKey || e.key === 'F12') {{
                                        e.preventDefault();
                                    }}
                                }}, true);
                                
                                // 추가 보안 레이어
                                video.addEventListener('loadedmetadata', () => {{
                                    video.style.filter = 'none';
                                }});
                                
                                // 캡처 방지
                                setInterval(() => {{
                                    if (document.pictureInPictureElement) {{
                                        document.exitPictureInPicture();
                                    }}
                                }}, 100);
                                
                                // 화면 녹화 방지
                                if (navigator.mediaDevices) {{
                                    navigator.mediaDevices.getDisplayMedia = undefined;
                                }}
                            }})();
                        </script>
                    </div>
                """
                st.markdown(video_html, unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        logout_time = datetime.now(timezone.utc)
        login_time = st.session_state.get('login_time')
        duration = round((logout_time - login_time).total_seconds() / 60) if login_time else 0
        
        logout_data = {
            "user_position": st.session_state.get('user_position'),
            "user_name": st.session_state.get('user_name'),
            "time": logout_time.isoformat(),
            "event": "logout",
            "duration": duration
        }
        
        requests.post(f"{st.secrets['supabase_url']}/rest/v1/login", headers={
            "Content-Type": "application/json",
            "apikey": st.secrets["supabase_key"],
            "Authorization": f"Bearer {st.secrets['supabase_key']}"
        }, json=logout_data)
        
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
else:
    st.error("로그인이 필요합니다.")
