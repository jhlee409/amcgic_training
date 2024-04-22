import streamlit as st
import time
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
        st.write("- 얘가 융통성이 없습니다. 너무 짧은 대답(예 n)을 넣거나, 빙빙 돌려서 대답하거나, 지시 대명사(거시기)를 많이 쓰면 잘 못알아 듣습니다.")
          
        # Function to list files in a specific directory in Firebase Storage
    def mp4_list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        file_names = []
        for blob in blobs:
            # Extracting file name from the path and adding to the list
            file_name = blob.name[len(directory):]  # Remove directory path from file name
            if file_name:  # Check to avoid adding empty strings (in case of directories)
                file_names.append(file_name)
        return file_names
    
    # esophagus or stomach selection
    folder_selection = st.sidebar.radio("Select Folder", ["초기화", "esophagus", "stomach", "duodenum"])

    if folder_selection == "초기화":
        directory_images = "EGD_Hemostasis_training/default/images/"
        directory_instructions = "EGD_Hemostasis_training/default/instructions/"
        st.session_state.prompt = ""
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state['messages'] = []
        #st.experimental_rerun()
    
    elif folder_selection == "esophagus":
        directory_images = "EGD_Hemostasis_training/esophagus/images/"
        directory_instructions = "EGD_Hemostasis_training/esophagus/instructions/"
    elif folder_selection == "stomach":
        directory_images = "EGD_Hemostasis_training/stomach/images/"
        directory_instructions = "EGD_Hemostasis_training/stomach/instructions/"
    else:
        directory_images = "EGD_Hemostasis_training/duodenum/images/"
        directory_instructions = "EGD_Hemostasis_training/duodenum/instructions/"

    st.sidebar.divider()

    # 선택한 동영상 파일을 세션 상태에 저장
    if 'selected_image_file' not in st.session_state:
        st.session_state.selected_image_file = None


    # List and select PNG files
    file_list_images = mp4_list_files('amcgi-bulletin.appspot.com', directory_images)
    selected_image_file = st.sidebar.selectbox(f"EGD 사진을 선택하세요.", file_list_images)

    if selected_image_file:
        if selected_image_file != st.session_state.selected_image_file:
            st.session_state.selected_image_file = selected_image_file
            selected_image_path = directory_images + selected_image_file
            # Firebase Storage 참조 생성
            bucket = storage.bucket('amcgi-bulletin.appspot.com')

            blob_a1 = bucket.blob(selected_image_path)
            expiration_time = datetime.utcnow() + timedelta(seconds=1600)
            video_url = blob_a1.generate_signed_url(expiration=expiration_time, method='GET')
            st.session_state.video_url = video_url

            # 동영상 플레이어 렌더링
            if 'video_url' in st.session_state:
                video_html = f'<video width="500" controls><source src="{st.session_state.video_url}" type="video/mp4"></video>'
                st.markdown(video_html, unsafe_allow_html=True)

    # Function to list files in a specific directory in Firebase Storage
    def list_files(bucket_name, directory):
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
    
    # List and select DOCX files
    file_list_instructions = list_files('amcgi-bulletin.appspot.com', directory_instructions)
    selected_instruction_file = st.sidebar.selectbox(f"case instruction 파일을 선택하세요.", file_list_instructions)

    # Read and display the content of the selected DOCX file
    if selected_instruction_file:
        full_path = directory_instructions + selected_instruction_file
        prompt = read_docx_file('amcgi-bulletin.appspot.com', full_path)
        st.session_state['prompt'] = prompt
        #st.text(prompt)  # Display the content of the docx file as text
        
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

    with st.spinner('열일 중...'):
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
        
else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 