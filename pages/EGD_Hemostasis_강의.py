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
          
    # Function to list files in a specific directory in Firebase Storage
    def prevideo_list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        file_names = []
        for blob in blobs:
            # Extracting file name from the path and adding to the list
            file_name = blob.name[len(directory):]  # Remove directory path from file name
            if file_name:  # Check to avoid adding empty strings (in case of directories)
                file_names.append(file_name)
        return file_names
    
    # Function to read file content from Firebase Storage
    def read_docx_file(bucket_name, file_name):
        try:
            bucket = storage.bucket(bucket_name)
            blob = bucket.blob(file_name)
            
            # 임시 파일을 메모리에서 처리
            content = blob.download_as_bytes()
            doc = docx.Document(io.BytesIO(content))
            
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            
            return '\n'.join(full_text)
        except Exception as e:
            st.error(f"문서를 읽는 중 오류가 발생했습니다: {str(e)}")
            return ""
           
    # esophagus or stomach selection
    folder_selection = st.sidebar.radio("선택 버튼", ["Default", "Hemostasis lecture", "cases"])

    # 동영상 플레이어를 렌더링할 컨테이너 생성
    pre_video_container = st.container()
    video_player_container = st.container()

    if folder_selection == "Default":
        directory_prevideos = "EGD_Hemostasis_training/default/prevideos/"
        directory_instructions = "EGD_Hemostasis_training/default/instructions/"
        directory_videos = "EGD_Hemostasis_training/default/videos/"
    elif folder_selection == "Hemostasis lecture":
        directory_prevideos = "EGD_Hemostasis_training/lecture/video/"
        directory_instructions = "EGD_Hemostasis_training/lecture/instruction/"
        directory_videos = "EGD_Hemostasis_training/lecture/videos/"
    elif folder_selection == "cases":
        directory_prevideos = "EGD_Hemostasis_training/cases/prevideos/"
        directory_instructions = "EGD_Hemostasis_training/cases/instructions/"
        directory_videos = "EGD_Hemostasis_training/cases/videos/"

    # 동영상 플레이어를 렌더링할 컨테이너 생성
    if 'prevideo_container' not in st.session_state:
        st.session_state.prevideo_container = st.container()
    if 'video_player_container' not in st.session_state:
        st.session_state.video_player_container = st.container()
    if 'instruction_container' not in st.session_state:
        st.session_state.instruction_container = st.container()

    # 라디오 버튼 선택이 변경될 때마다 동영상 플레이어와 컨텐츠 제거
    if st.session_state.get('previous_folder_selection', None) != folder_selection:
        # 상태 초기화
        st.session_state.previous_folder_selection = folder_selection
        st.session_state.selected_prevideo_file = None
        st.session_state.prevideo_url = None
        
        # 모든 컨테이너 비우기
        st.session_state.prevideo_container.empty()
        st.session_state.video_player_container.empty()
        st.session_state.instruction_container.empty()
        
        # 페이지 새로고침
        st.rerun()

    # List and select prevideo files
    file_list_prevideo = prevideo_list_files('amcgi-bulletin.appspot.com', directory_prevideos)
    selected_prevideo_file = st.sidebar.selectbox(f"파일 제목을 선택하세요..", file_list_prevideo)

    # 선택된 파일이 있을 때만 instruction 파일 이름 생성
    if selected_prevideo_file:
        instruction_file_name = os.path.splitext(selected_prevideo_file)[0] + '.docx'
        selected_instruction_file = directory_instructions + instruction_file_name
        
        # Default 폴더인 경우 아무 작업도 하지 않음
        if folder_selection == "Default":
            pass
    else:
        instruction_file_name = None
        selected_instruction_file = None

    # 선택된 파일이 변경되었을 때
    if selected_prevideo_file != st.session_state.get('selected_prevideo_file', ''):
        # 모든 컨테이너 비우기
        st.session_state.prevideo_container.empty()
        st.session_state.video_player_container.empty()
        st.session_state.instruction_container.empty()
        
        st.session_state.selected_prevideo_file = selected_prevideo_file
        selected_prevideo_path = directory_prevideos + selected_prevideo_file
        
        # Firebase Storage 참조 생성
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        blob = bucket.blob(selected_prevideo_path)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
        prevideo_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
        st.session_state.prevideo_url = prevideo_url

        # 선택한 pre_video와 같은 이름의 mp4 파일 찾기
        video_name = os.path.splitext(selected_prevideo_file)[0] + '_main' + '.mp4'
        selected_video_file = directory_videos + video_name
        st.session_state.selected_video_file = selected_video_file  # 세션 상태에 저장
        
        # 선택한 pre_video와 같은 이름의 docx 파일 찾기
        instruction_file_name = os.path.splitext(selected_prevideo_file)[0] + '.docx'
        selected_instruction_file = directory_instructions + instruction_file_name
        
        # Read and display the content of the selected DOCX file
        if selected_instruction_file:
            try:
                with st.session_state.instruction_container:  # instruction 컨테이너 사용
                    full_path = selected_instruction_file
                    prompt = read_docx_file('amcgi-bulletin.appspot.com', full_path)
                    if prompt:  # 내용이 있는 경우에만 표시
                        prompt_lines = prompt.split('\n')
                        prompt_markdown = '\n'.join(prompt_lines)
                        st.markdown(prompt_markdown)
            except Exception as e:
                st.error(f"문서 처리 중 오류가 발생했습니다: {str(e)}")
        

        # 새로운 동영상 플레이어 렌더링        
        with st.session_state.prevideo_container:
            video_html = f'<video width="500" height="500" controls><source src="{st.session_state.prevideo_url}" type="video/mp4"></video>'
            st.markdown(video_html, unsafe_allow_html=True)

    # '진행' 버튼 추가
    if st.sidebar.button('진행'):
        # 사용자 이름과 직책과 접속 날짜 기록
        user_name = st.session_state.get('user_name', 'unknown')
        user_position = st.session_state.get('user_position', 'unknown')
        access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 파일 이름에서 확장자(.mp4) 제거
        file_name_without_extension = os.path.splitext(selected_prevideo_file)[0]

        # '_video' 글자와 확장자를 제거한 파일 이름 생성
        file_name_without_extension_and_video = file_name_without_extension.replace('_main', '')
        # 로그 내용을 문자열로 생성
        log_entry = f"사용자: {user_name}\n직급: {user_position}\n날짜: {access_date}\n메뉴: {file_name_without_extension_and_video}\n"

        # Firebase Storage에 로그 파일 업로드
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        log_blob = bucket.blob(f'log_EGD_Hemostasis/{user_position}*{user_name}*{file_name_without_extension}')
        log_blob.upload_from_string(log_entry, content_type='text/plain')

        if st.session_state.get('selected_video_file'):
            # Firebase Storage 참조 생성
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            blob = bucket.blob(st.session_state.selected_video_file)
            expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
            video_url = blob.generate_signed_url(expiration=expiration_time, method='GET')

            # 비디오 플레이어 삽입
            with st.session_state.video_player_container:
                video_html = f'<video width="1000" height="800" controls><source src="{video_url}" type="video/mp4"></video>'
                st.markdown(video_html, unsafe_allow_html=True)

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
            "user_position": st.session_state.get('user_position'),
            "user_name": st.session_state.get('user_name'),
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

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")