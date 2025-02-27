import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta, timezone
import requests
import os

# Set page to wide mode
st.set_page_config(page_title="Dx EUS 강의", layout="wide")

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
st.subheader("진단 EUS 강의 모음")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("- 이 강의 모음은 진단 EUS 강의 동영상 모음입니다.")
    st.write("- 왼쪽에서 시청하고자 하는 강의를 선택한 후 prevvideo가 나타나면 '본강의 시청' 버튼을 누르세요. 그러면 본강의를 시청할 수 있습니다.")
    st.write("- 화면을 클릭하면 play 되고, 화면 왼쪽 아래 전체 화면 버튼 누르면 전체 화면을 볼 수 있습니다.")
    st.write("- 다른 강의를 보려면 우선 Default를 선택해서 이전 강의 화면을 지운 후, 다른 강의를 선택해야 합니다. 그냥 다른 강의 선택하면 화면이 안넘어 갑니다.")
    st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")

# 강의 목록
lectures = ["Default", "EUS_basic", "EUS_SET", "EUS_case"]

# 사이드바에서 강의 선택
selected_lecture = st.sidebar.selectbox("먼저 Default 선택해서 이전 화면 지운 후 다음 강의를 선택하세요", lectures, key='lecture_selector')

# 선택이 바뀌었는지 확인하기 위해 previous_lecture 사용
if 'previous_lecture' not in st.session_state:
    st.session_state['previous_lecture'] = None

# 만약 강의가 바뀌었다면, prevideo_url / docx_content / main_video_url / show_main_video 모두 초기화
if st.session_state['previous_lecture'] != selected_lecture:
    st.session_state['show_main_video'] = False
    st.session_state['prevideo_url'] = None
    st.session_state['docx_content'] = None
    st.session_state['main_video_url'] = None

# 이제 현재 선택을 previous_lecture에 업데이트
st.session_state['previous_lecture'] = selected_lecture

# 2:3 비율의 두 컬럼 생성
left_col, right_col = st.columns([1, 14])

# Lectures 폴더 내 mp4/docx 파일 경로 설정
directory_lectures = "Lectures/"
bucket_name = 'amcgi-bulletin.appspot.com'
bucket = storage.bucket(bucket_name)
expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)

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

        # Blob 가져오기
        prevideo_blob = bucket.blob(prevideo_path)
        docx_blob = bucket.blob(docx_path)
        main_video_blob = bucket.blob(main_video_path)

        # 왼쪽 컬럼에 prevideo와 docx 내용 표시
        with left_col:
            # 미리보기 영상
            if prevideo_blob.exists():
                prevideo_url = prevideo_blob.generate_signed_url(expiration=expiration_time, method='GET')
                st.session_state['prevideo_url'] = prevideo_url

                video_html = f'''
                <div style="display: flex; justify-content: center;">
                    <video width="50px" controls controlsList="nodownload">
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
            else:
                st.warning(f"미리보기 영상({prevideo_name})을 찾을 수 없습니다.")

            # DOCX 자료
            if docx_blob.exists():
                docx_content = docx_blob.download_as_bytes()
                doc = docx.Document(io.BytesIO(docx_content))
                text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                st.session_state['docx_content'] = text_content
                st.write(text_content)
            else:
                st.warning(f"강의 자료({docx_name})를 찾을 수 없습니다.")

        # 오른쪽 컬럼(본강의 영상)
        with right_col:
            if st.session_state.get('show_main_video', False):
                if main_video_blob.exists():
                    main_video_url = main_video_blob.generate_signed_url(expiration=expiration_time, method='GET')
                    st.session_state['main_video_url'] = main_video_url

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
                else:
                    st.warning(f"본 강의 영상({main_video_name})을 찾을 수 없습니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")

# 사이드바에 본강의 시청 버튼
if st.sidebar.button("본강의 시청"):
    # 본강의 보이도록 플래그 설정
    st.session_state['show_main_video'] = True

    # 로그 파일 생성 및 전송
    if selected_lecture != "Default":
        name = st.session_state.get('name', 'unknown')
        position = st.session_state.get('position', 'unknown')
        access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        log_entry = f"Position: {position}, Name: {name}, Access Date: {access_date}, EUS강의: {selected_lecture}\n"

        log_blob = bucket.blob(
            f'log_EUS/{position}*{name}*{selected_lecture}'
        )
        log_blob.upload_from_string(log_entry, content_type='text/plain')
    
    # 화면 갱신
    st.rerun()

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