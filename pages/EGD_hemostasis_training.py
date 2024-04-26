import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta

# Set page to wide mode
st.set_page_config(page_title="EGD_Hemostasis_training", layout="wide")

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
    st.subheader("EGD_Hemostasis_training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 가장 먼저 왼쪽 sidebar에서 default는 '초기화'입니다. 잠시 기다렸다가 esophagus, stomach, duodenum 중 한 가지를 선택합니다.")
        st.write("- 얘가 융통성이 없습니다. 관련없는 엉뚱한 대답을 넣거나, 빙빙 돌려서 대답하거나, 지시 대명사(거시기)를 많이 쓰면 잘 못알아 듣습니다.")
          
    # Function to list files in a specific directory in Firebase Storage
    def pre_videos_list_files(bucket_name, directory):
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
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Download the file to a temporary location
        temp_file_path = "/tmp/tempfile.docx"
        blob.download_to_filename(temp_file_path)
        
        # Read the content of the DOCX file
        doc = docx.Document(temp_file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        
        # Join the text into a single string
        return '\n'.join(full_text)
    
    # esophagus or stomach selection
    folder_selection = st.sidebar.radio("선택 버튼", ["초기화", "esophagus", "stomach", "duodenum"])
    
    directory_videos = "EGD_Hemostasis_training/videos/"

    if folder_selection == "초기화":
        directory_pre_videos = "EGD_Hemostasis_training/default/pre_videos/"
        directory_instructions = "EGD_Hemostasis_training/default/instructions/"
        if 'show_expander' in st.session_state:
            del st.session_state['show_expander']
    
    elif folder_selection == "esophagus":
        directory_pre_videos = "EGD_Hemostasis_training/esophagus/pre_videos/"
        directory_instructions = "EGD_Hemostasis_training/esophagus/instructions/"
    elif folder_selection == "stomach":
        directory_pre_videos = "EGD_Hemostasis_training/stomach/pre_videos/"
        directory_instructions = "EGD_Hemostasis_training/stomach/instructions/"
    else:
        directory_pre_videos = "EGD_Hemostasis_training/duodenum/pre_videos/"
        directory_instructions = "EGD_Hemostasis_training/duodenum/instructions/"

    st.sidebar.divider()

    # 선택한 동영상 파일을 세션 상태에 저장
    if 'selected_pre_videos_file' not in st.session_state:
        st.session_state.selected_pre_videos_file = None


    # List and select PNG files
    file_list_pre_videos = pre_videos_list_files('amcgi-bulletin.appspot.com', directory_pre_videos)
    selected_pre_videos_file = st.sidebar.selectbox(f"pre_video를 선택하세요.", file_list_pre_videos)

    # 동영상 플레이어를 렌더링할 컨테이너 생성
    pre_video_container = st.container()

    if selected_pre_videos_file:
        if selected_pre_videos_file != st.session_state.get('selected_pre_videos_file', ''):
            st.session_state.selected_pre_videos_file = selected_pre_videos_file
            selected_pre_videos_path = directory_pre_videos + selected_pre_videos_file
            
            # Firebase Storage 참조 생성
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            blob = bucket.blob(selected_pre_videos_path)
            expiration_time = datetime.utcnow() + timedelta(seconds=1600)
            pre_video_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
            st.session_state.pre_video_url = pre_video_url
            
            # 선택한 pre_video와 같은 이름의 docx 파일 찾기
            instruction_file_name1 = os.path.splitext(selected_pre_videos_file)[0] + '_1.docx'
            selected_instruction_file1 = directory_instructions + instruction_file_name1
            
            instruction_file_name2 = os.path.splitext(selected_pre_videos_file)[0] + '_2.docx'
            selected_instruction_file2 = directory_instructions + instruction_file_name2
            
            # 선택한 pre_video와 같은 이름의 mp4 파일 찾기
            video_name = os.path.splitext(selected_pre_videos_file)[0] + '_2' + '.mp4'
            selected_video_file = directory_videos + video_name
            st.session_state.selected_video_file = selected_video_file  # 세션 상태에 저장
            
            # Read and display the content of the selected DOCX file
            if selected_instruction_file1:
                full_path1 = selected_instruction_file1
                prompt1 = read_docx_file('amcgi-bulletin.appspot.com', full_path1)
                prompt1_lines = prompt1.split('\n')  # 내용을 줄 바꿈 문자로 분리
                prompt1_markdown = '\n'.join(prompt1_lines)  # 분리된 내용을 다시 합치면서 줄 바꿈 적용
                st.markdown(prompt1_markdown)
            
            # 이전 동영상 플레이어 지우기
            pre_video_container.empty()
            
        # 새로운 동영상 플레이어 렌더링
        with pre_video_container:
            video_html = f'<video width="500" controls><source src="{st.session_state.pre_video_url}" type="video/mp4"></video>'
            st.markdown(video_html, unsafe_allow_html=True)
            
            instruction_file_name1 = os.path.splitext(selected_pre_videos_file)[0] + '_1.docx'
            selected_instruction_file1 = directory_instructions + instruction_file_name1

            instruction_file_name2 = os.path.splitext(selected_pre_videos_file)[0] + '_2.docx'
            selected_instruction_file2 = directory_instructions + instruction_file_name2

            # '진행' 버튼 추가
            if st.sidebar.button('진행'):
                if selected_instruction_file1:
                    full_path1 = selected_instruction_file1
                    prompt1 = read_docx_file('amcgi-bulletin.appspot.com', full_path1)
                    prompt1_lines = prompt1.split('\n')  # 내용을 줄 바꿈 문자로 분리
                    prompt1_markdown = '\n'.join(prompt1_lines)  # 분리된 내용을 다시 합치면서 줄 바꿈 적용
                    st.markdown(prompt1_markdown)
                
                if selected_instruction_file2:
                    full_path2 = selected_instruction_file2
                    prompt2 = read_docx_file('amcgi-bulletin.appspot.com', full_path2)
                    prompt2_lines = prompt2.split('\n')  # 내용을 줄 바꿈 문자로 분리
                    prompt2_markdown = '\n'.join(prompt2_lines)  # 분리된 내용을 다시 합치면서 줄 바꿈 적용
                    
                    # 새로운 컨테이너에 file2의 내용 출력
                    with st.container():
                        st.markdown(prompt2_markdown)  # Display the content of the docx file with line breaks
                
                st.session_state['show_expander'] = True

    st.sidebar.divider()

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감
                    
    # 'play' 버튼 대신 expander 추가
    if st.session_state.get('show_expander'):
        video_expander = st.expander('실제 지혈술 동영상을 보시려면 여기를 클릭해 주세요')
        with video_expander:
            if st.session_state.get('selected_video_file'):  # 세션 상태에서 가져오기
                # Firebase Storage 참조 생성
                bucket = storage.bucket('amcgi-bulletin.appspot.com')
                blob = bucket.blob(st.session_state.selected_video_file)
                expiration_time = datetime.utcnow() + timedelta(seconds=1600)
                video_url = blob.generate_signed_url(expiration=expiration_time, method='GET')

                # expander 내부에 비디오 플레이어 삽입
                video_html = f'''
                    <video id="video_player" width="500" controls controlsList="nodownload">
                        <source src="{video_url}" type="video/mp4">
                    </video>
                    <script>
                        var video_player = document.getElementById('video_player');
                        video_player.addEventListener('contextmenu', function(e) {{
                            e.preventDefault();
                        }});
                    </script>
                '''
                st.components.v1.html(video_html, height=450)
    
    if folder_selection == "초기화":
        if 'show_expander' in st.session_state:
            del st.session_state['show_expander']
        
else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 