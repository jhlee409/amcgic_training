import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime

# Set page to wide mode
st.set_page_config(page_title="PBL", page_icon=":robot_face:", layout="wide")

if st.session_state.get('logged_in'):
    
    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    # Initialize prompt variable
    prompt = ""

    client = OpenAI()

    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []

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
    
    # Function to get file content from Firebase Storage
    def get_file_content(bucket_name, directory, file_name):
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(directory + file_name)
        return blob.download_as_bytes()

    # 메인 컨텐츠와 메시지 창을 위한 컨테이너 생성
    main_container = st.container()
    message_container = st.container()

    # 레이아웃 조정
    col1, col2 = st.columns([3, 1])

    with col1:
        # 메시지 창 컨테이너 생성
        message_container = st.container()

        # 메시지 창 컨테이너에 테두리 추가
        message_container.markdown(
            """
            <style>
            .message-container {
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                height: 600px;
                overflow-y: auto;
            }
            .message-container p {
                text-align: left;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # 메시지 창 생성
        message_box = message_container.empty()

        # 메시지 창 생성
        if 'message_box' not in st.session_state:
            st.session_state.message_box = ""

    with col2:
        # Streamlit Sidebar with Dropdown for file selection
        case_directory = "PBL/cases/"
        case_file_list = list_files('amcgi-bulletin.appspot.com', case_directory)
        selected_case_file = st.sidebar.selectbox("증례 파일을 선택하세요.", case_file_list)

        # Read content of the selected case file and store in prompt variable
        if selected_case_file:
            # 사용자 이메일과 접속 날짜 기록
            user_email = st.session_state.get('user_email', 'unknown')  # 세션에서 이메일 가져오기
            access_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)

            # 로그 내용을 문자열로 생성
            log_entry = f"Email: {user_email}, Access Date: {access_date}, Menu: {selected_case_file}\n"

            # Firebase Storage에 로그 파일 업로드
            bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
            log_blob = bucket.blob(f'logs/{user_email}_{access_date}_{selected_case_file}.txt')  # 로그 파일 경로 설정
            log_blob.upload_from_string(log_entry, content_type='text/plain')  # 문자열로 업로드

            # Include the directory in the path when reading the file
            case_full_path = case_directory + selected_case_file
            prompt = read_docx_file('amcgi-bulletin.appspot.com', case_full_path)
            st.session_state['prompt'] = prompt
           
        # Manage thread id
        if 'thread_id' not in st.session_state:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

        thread_id = st.session_state.thread_id

        assistant_id = "asst_MPsBiEOCzmgElfGwHf757F1b"

        # Display Form Title
        main_container.subheader("AMC GI C:&emsp;PBL 챗봇")
        with main_container.expander("정상적이 작동을 위해, 반드시 먼저 여길 눌러서 사용방법을 읽어 주세요."):
            st.write("- 처음에는 왼쪽 sidebar에서 증례 파일을 선택해 주세요.")
            st.write("- case가 준비되면 '어떤 환자인가요?'로 질문을 시작하세요.")

    # col1과 col2 아래에 입력창 추가
    input_container = st.container()
    with input_container:
        user_input = st.chat_input("입력창입니다. 선생님의 message를 여기에 입력하고 엔터를 치세요")

    st.write(assistant_id)
    
    # 사용자 입력이 있을 경우에만 메시지 생성 및 사용
    if user_input:
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )
        
#         # message 변수가 정의된 후에만 사용
#         if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
#             if messages.data[0].role == "assistant":
#                 st.session_state.message_box += f"🤖: {messages.data[0].content[0].text.value}\n\n"

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
    
    st.write(assistant_id)

    #메세지 모두 불러오기
    thread_messages = client.beta.threads.messages.list(thread_id, order="asc")

    st.sidebar.divider()

    # Clear button in the sidebar
    if st.sidebar.button('이전 대화기록 삭제 버튼'):
        # Reset the prompt, create a new thread, and clear the docx_file and messages
        prompt = []
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state['messages'] = []
        for msg in thread_messages.data:
            msg.content[0].text.value=""
        # Clear the message box in col2
        st.session_state.message_box = ""
        message_container.markdown("", unsafe_allow_html=True)

#     # assistant 메시지를 메시지 창에 추가
#     if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
#         if messages.data[0].role == "assistant":
#             st.session_state.message_box += f"🤖: {messages.data[0].content[0].text.value}\n\n"
#         else:
#             st.session_state.message_box += f"**{messages.data[0].role}:** {messages.data[0].content[0].text.value}\n\n"
#         message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)

#     st.sidebar.divider()
#     # 로그아웃 버튼 생성
#     if st.sidebar.button('로그아웃'):
#         st.session_state.logged_in = False
#         st.rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

# else:
#     # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
#     st.error("로그인이 필요합니다.")
