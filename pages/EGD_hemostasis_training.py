import streamlit as st
import time
import os
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta

# Set page to wide mode
st.set_page_config(page_title="EGD_Hemostasis_training", layout="wide")

if st.session_state.get('logged_in'):

    # Initialize prompt variable
    prompt = ""      

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

    client = OpenAI()

    # Display Form Title
    st.subheader("EGD_Hemostasis_training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 가장 먼저 왼쪽 sidebar에서 default는 '초기화'입니다. 잠시 기다렸다가 esophagus, stomach, duodenum 중 한 가지를 선택합니다.")
        st.write("- 그 아래에서 pre_video를 선택해서 기다리시면 화면에 안내가 나옵니다. 그 안내를 따라가시면 됩니다.")
        st.write("- 마지막에 실제 지혈술의 동영상을 보려면 왼쪽 sidebar에 'play' 버튼을 누르시면 됩니다.")
        st.write("- 한 증례가 끝나고 다음 증례로 넘어가시려면, 먼저 왼쪽의 '초기화' 버튼을 선택하여 초기화 하고, 처음 과정부터 다시 시작하시면 됩니다.")
        st.write("- 각 단계마다 반드시 '열일 중이니 기다려 주세요...' 스핀이 멈출 때까지 기다리세요. 스핀 돌고있는 도중에 다른 버튼 누르면 오류납니다.")
        st.write("- 마지막 과정의 '열일 중이니 기다려 주세요...' 메시지가 특히 오래 걸립니다. 1분이 걸리 수도 있는데, 고장난 것 아닙니다.")
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
        st.session_state.prompt = ""
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state['messages'] = []
        #st.experimental_rerun()
    
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
            instruction_file_name = os.path.splitext(selected_pre_videos_file)[0] + '.docx'
            selected_instruction_file = directory_instructions + instruction_file_name
            
            # 선택한 pre_video와 같은 이름의 mp4 파일 찾기
            video_name = os.path.splitext(selected_pre_videos_file)[0] + '_2' + '.mp4'
            selected_video_file = directory_videos + video_name
            st.session_state.selected_video_file = selected_video_file  # 세션 상태에 저장
            
            # Read and display the content of the selected DOCX file
            if selected_instruction_file:
                full_path = selected_instruction_file
                prompt = read_docx_file('amcgi-bulletin.appspot.com', full_path)
                st.session_state['prompt'] = prompt
                #st.text(prompt)  # Display the content of the docx file as text
            
            # 이전 동영상 플레이어 지우기
            pre_video_container.empty()
            
        # 새로운 동영상 플레이어 렌더링
        with pre_video_container:
            video_html = f'<video width="500" controls><source src="{st.session_state.pre_video_url}" type="video/mp4"></video>'
            st.markdown(video_html, unsafe_allow_html=True)
            
        # '진행' 버튼 추가
        if st.sidebar.button('진행'):
            # 사용자 입력 창에 'y' 입력 및 엔터 효과 적용
            user_input = 'y'
            prompt = user_input
        
        # # 'play' 버튼 추가
        # if st.sidebar.button('Play'):
        #     if st.session_state.get('selected_video_file'):  # 세션 상태에서 가져오기
        #         # Firebase Storage 참조 생성
        #         bucket = storage.bucket('amcgi-bulletin.appspot.com')
        #         blob = bucket.blob(st.session_state.selected_video_file)
        #         expiration_time = datetime.utcnow() + timedelta(seconds=1600)
        #         video_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
                
        #         # 재생 속도 선택 옵션
        #         playback_speeds = [1.0, 1.5, 2.0, 3.0]
        #         selected_speed = st.sidebar.selectbox("재생 속도 선택", playback_speeds)
                
        #         # 새 윈도우에서 비디오 재생
        #         js_code = f"""
        #             <script>
        #                 var video_url = '{video_url}';
        #                 var selected_speed = {selected_speed};
                        
        #                 var video_window = window.open('', '_blank', 'width=1600,height=1200');
        #                 video_window.document.write('<video id="video_player" width="100%" height="100%" controls><source src="' + video_url + '" type="video/mp4"></video>');
                        
        #                 var video_player = video_window.document.getElementById('video_player');
        #                 video_player.playbackRate = selected_speed;
        #             </script>
        #         """
        #         st.components.v1.html(js_code, height=0)

    st.sidebar.divider()

    # Manage thread id
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    thread_id = st.session_state.thread_id

    assistant_id = "asst_AyqS2LqfxPw2RwRV1sl1bGhd"

    # Get user input from chat nput
    user_input = st.chat_input("입력창입니다. 선생님의 message를 여기에 입력하고 엔터를 치세요")

    # 사용자 입력이 있을 경우, prompt를 user_input으로 설정
    if user_input:
        if user_input.strip():  # Check if user_input is not empty or whitespace
            prompt = user_input
        else:
            print("Please enter a non-empty prompt.")
            # Handle the case when user_input is empty or whitespace
            # You can prompt the user to enter a valid input or take appropriate action
    else:
        print("No user input provided.")
        # Handle the case when user_input is None or not provided
        # You can prompt the user to enter a valid input or take appropriate action

    if prompt:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )

    # # 입력한 메세지 UI에 표시
    # if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    #     with st.chat_message(message.role):
    #         st.write(message.content[0].text.value)

    #RUN을 돌리는 과정
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    with st.spinner('열일 중이니 기다려 주세요...'):
        #RUN이 completed 되었나 1초마다 체크
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

    #while문을 빠져나왔다는 것은 완료됐다는 것이니 메세지 불러오기
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )

    # # assistant 메세지 UI에 추가하기
    # #if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    # with st.chat_message(messages.data[0].role):
    #     st.write(messages.data[0].content[0].text.value)

    #메세지 모두 불러오기
    thread_messages = client.beta.threads.messages.list(thread_id, order="asc")

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

    for msg in thread_messages.data:
        # 메시지 내용 확인 및 필터링 조건 추가
        if msg.content and msg.content[0].text.value:
            content = msg.content[0].text.value
            # 필터링 조건: 내용이 비어있지 않고, '..', '...', '전체 지시 사항'을 포함하지 않는 경우에만 UI에 표시
            if content.strip() not in ['', '..', '...'] and '전체 지시 사항' not in content:
                with st.chat_message(msg.role):
                    st.write(content)
                    
    # 'play' 버튼 대신 expander 추가
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
                <video id="video_player" width="500" controls>
                    <source src="{video_url}" type="video/mp4">
                </video>
                <script>
                    var video_player = document.getElementById('video_player');
                </script>
            '''
            st.components.v1.html(video_html, height=450)
        
        
else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 