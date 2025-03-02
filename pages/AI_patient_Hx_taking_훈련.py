import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta, timezone
import requests
import os
import tempfile

# Set page to wide mode
st.set_page_config(page_title="AI Hx. taking", page_icon=":robot_face:", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()

# Initialize session state variables
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Initialize prompt variable
prompt = ""

client = OpenAI()

# Assistant ID 설정
assistant_id = "asst_ecq1rotgT4c3by2NJBjoYcKj"  # AI 환자 병력 청취 assistant

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
    case_directory = "AI_patient_Hx_taking/case/"
    case_file_list = list_files('amcgi-bulletin.appspot.com', case_directory)
    selected_case_file = st.sidebar.selectbox("증례 파일을 선택하세요.", case_file_list)

    # Read content of the selected case file and store in prompt variable
    if selected_case_file:
        # 000.docx 파일은 로그를 생성하지 않음
        if selected_case_file != "00.docx":
            # 사용자 이름과 직책과 접속 날짜 기록
            name = st.session_state.get('name', 'unknown')
            position = st.session_state.get('position', 'unknown')
            access_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # '.docx' 확장자를 제거한 파일 이름
            file_name_without_extension = selected_case_file.replace('.docx', '')

            # 로그 내용을 문자열로 생성
            log_entry = f"직급: {position}\n사용자: {name}\n메뉴: {file_name_without_extension}\n날짜: {access_date}\n"

            # Firebase Storage에 로그 파일 업로드
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            log_blob = bucket.blob(f'log_AI_patient_Hx_taking/{position}*{name}*{file_name_without_extension}')
            log_blob.upload_from_string(log_entry, content_type='text/plain')

        # Include the directory in the path when reading the file
        case_full_path = case_directory + selected_case_file
        prompt = read_docx_file('amcgi-bulletin.appspot.com', case_full_path)
        st.session_state['prompt'] = prompt

        # Find the corresponding Excel file in the reference directory
        reference_directory = "AI_patient_Hx_taking/reference/"
        reference_file_list = list_files('amcgi-bulletin.appspot.com', reference_directory)
        excel_file = selected_case_file.replace('.docx', '.xlsx')
        if excel_file in reference_file_list:
            file_content = get_file_content('amcgi-bulletin.appspot.com', reference_directory, excel_file)
            st.sidebar.download_button(
                label="Case 해설 자료 다운로드",
                data=file_content,
                file_name=excel_file,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            st.sidebar.warning("해당하는 엑셀 파일이 없습니다.")
        
    # Manage thread id
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    thread_id = st.session_state.thread_id

    # Display Form Title
    main_container.subheader("AMC GI:&emsp;AI 환자 병력 청취 훈련 챗봇&emsp;&emsp;&emsp;v 1.5.0")
    with main_container.expander("정상적이 작동을 위해, 반드시 먼저 여길 눌러서 사용방법을 읽어 주세요."):
        st.write("- 처음에는 왼쪽 sidebar에서 증례 파일을 선택해 주세요.")
        st.write("- case가 준비되면 '어디가 불편해서 오셨나요?'로 문진을 시작하세요.")
        st.write("- 문진을 마치는 질문은 '알겠습니다. 혹시 궁금한 점이 있으신가요?' 입니다.")
        st.write("- 마지막에는 선생님이 물어보지 않은 중요 항목을 보여주게 되는데, 이 과정이 좀 길게 걸릴 수 있으니, 기다려 주세요.^^")
        st.write("- 다른 증례를 선택하기 전에 반드시 '이전 대화기록 삭제버튼'을  한 번 누른 후 다른 증례를 선택하세요. 안그러면 이전 증례의 기록이 남아 있게 됩니다.")
        st.write("- 증례 해설 자료가 필요하시면 다운로드 하실 수 있는데, 전체가 refresh 되므로 도중에 다운로드 하지 마시고, 마지막에 다운로드해 주세요.")
        st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")

# col1과 col2 아래에 입력창 추가
input_container = st.container()
with input_container:
    user_input = st.chat_input("입력창입니다. 선생님의 message를 여기에 입력하고 엔터를 치세요")

# 사용자 입력이 있을 경우, prompt를 user_input으로 설정
if user_input:
    prompt = user_input

message = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=prompt
)
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

# assistant 메시지를 메시지 창에 추가
if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    if messages.data[0].role == "assistant":
        st.session_state.message_box += f"🤖: {messages.data[0].content[0].text.value}\n\n"
    else:
        st.session_state.message_box += f"**{messages.data[0].role}:** {messages.data[0].content[0].text.value}\n\n"
    message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)

st.sidebar.divider()

if st.sidebar.button("Logout"):
    # 로그아웃 시간과 duration 계산
    logout_time = datetime.now(timezone.utc)
    login_time = st.session_state.get('login_time')
    if login_time:
        if not login_time.tzinfo:
            login_time = login_time.replace(tzinfo=timezone.utc)
        duration = round((logout_time - login_time).total_seconds())
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
    
    try:
        # 현재 시간 가져오기 (초 단위까지)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        position = st.session_state.get('position', '')
        name = st.session_state.get('name', '')
        
        # Firebase Storage 버킷 가져오기
        bucket = storage.bucket()
        
        # 로그인 시간 가져오기
        login_timestamp = None
        login_blobs = list(bucket.list_blobs(prefix="log_login/"))
        
        # 현재 사용자의 가장 최근 로그인 찾기
        for blob in sorted(login_blobs, key=lambda x: x.name, reverse=True):
            try:
                # 임시 파일에 다운로드
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    with open(temp_file.name, 'r') as f:
                        content = f.read()
                    os.unlink(temp_file.name)
                
                # 로그 내용 파싱
                parts = content.split('*')
                if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                    login_timestamp = datetime.strptime(parts[3], '%Y-%m-%d %H:%M:%S')
                    # 타임존 정보 추가
                    login_timestamp = login_timestamp.replace(tzinfo=timezone.utc)
                    # 로그인 파일 찾았으므로 삭제
                    blob.delete()
                    break
            except Exception as e:
                st.error(f"로그인 로그 파일 처리 중 오류 발생: {str(e)}")
        
        # 로그아웃 로그 파일 생성 및 업로드
        now = datetime.now(timezone.utc)
        log_content = f"{position}*{name}*logout*{now.strftime('%Y-%m-%d %H:%M:%S')}"
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write(log_content)
            temp_file_path = temp_file.name
        
        log_filename = f"log_logout/{timestamp}"
        blob = bucket.blob(log_filename)
        blob.upload_from_filename(temp_file_path)
        
        # 시간 차이 계산 및 duration 로그 생성
        if login_timestamp:
            # login_timestamp에 타임존 정보가 없으면 추가
            if not login_timestamp.tzinfo:
                login_timestamp = login_timestamp.replace(tzinfo=timezone.utc)
            time_diff_seconds = int((now - login_timestamp).total_seconds())
            
            # duration 로그 파일 생성 및 업로드
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(f"{position}*{name}*{time_diff_seconds}*{now.strftime('%Y-%m-%d %H:%M:%S')}")
                duration_temp_path = temp_file.name
            
            duration_filename = f"log_duration/{position}*{name}*{time_diff_seconds}*{timestamp}"
            duration_blob = bucket.blob(duration_filename)
            duration_blob.upload_from_filename(duration_temp_path)
            os.unlink(duration_temp_path)
        
        # 로그아웃 로그 파일 삭제 (업로드 후)
        os.unlink(temp_file_path)
        
        # 모든 로그아웃 로그 파일 삭제
        logout_blobs = list(bucket.list_blobs(prefix="log_logout/"))
        for blob in logout_blobs:
            try:
                # 현재 사용자의 로그아웃 파일만 삭제
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    with open(temp_file.name, 'r') as f:
                        content = f.read()
                    os.unlink(temp_file.name)
                
                parts = content.split('*')
                if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                    blob.delete()
            except Exception as e:
                st.error(f"로그아웃 로그 파일 삭제 중 오류 발생: {str(e)}")
        
    except Exception as e:
        st.error(f"로그 파일 처리 중 오류 발생: {str(e)}")
    
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")