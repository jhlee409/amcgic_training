import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="AI Hx. taking", page_icon=":robot_face:", layout="wide")

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

    # Streamlit Sidebar with Dropdown for file selection
    case_directory = "AI_patient_Hx_taking/case/"
    case_file_list = list_files('amcgi-bulletin.appspot.com', case_directory)
    selected_case_file = st.sidebar.selectbox("증례 파일을 선택하세요.", case_file_list)

    # Read content of the selected case file and store in prompt variable
    if selected_case_file:
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
        
        # 새로운 case 선택 시 이전 대화 기록 자동 삭제
        if 'thread_id' in st.session_state:
            thread_messages = client.beta.threads.messages.list(st.session_state.thread_id, order="asc")
            for msg in thread_messages.data:
                msg.content[0].text.value = ""
            st.session_state['messages'] = []

    # Manage thread id
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    thread_id = st.session_state.thread_id

    assistant_id = "asst_ecq1rotgT4c3by2NJBjoYcKj"

    # Display Form Title
    st.subheader("AMC GI:&emsp;AI 환자 병력 청취 훈련 챗봇&emsp;&emsp;&emsp;v 1.5.0")
    with st.expander("정상적이 작동을 위해, 반드시 먼저 여길 눌러서 사용방법을 읽어 주세요."):
        st.write("- 왼쪽 sidebar에서 증례 파일을 선택해 주세요.")
        st.write("- AI가 '선생님, 처음 뵙겠습니다. 잘 부탁드립니다.'라고 하면 '어디가 불편해서 오셨나요?'로 문진을 시작하세요.")
        st.write("- 문진을 마치는 질문은 '알겠습니다. 혹시 궁금한 점이 있으신가요?' 입니다.")
        st.write("- 마지막에는 선생님이 물어보지 않은 중요 항목을 보여주게 되는데, 결과가 늦게 나올 수 있습니다. 참을성을 가지고 기다려 주세요.^^")
        st.write("- 증례 해설 자료가 필요하시면 다운로드 하실 수 있는데, 전체가 refresh 되므로 도중에 다울로드 하지 마시고, 마지막에 다운로드 받아주세요.")
    st.divider()

    # Get user input from chat input
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

    st.sidebar.divider()
            
    # # assistant 메세지 UI에 추가하기
    # if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    #     with st.chat_message(messages.data[0].role):
    #         st.write(messages.data[0].content[0].text.value)

    for msg in thread_messages.data:
        # 메시지 내용 확인 및 필터링 조건 추가
        if msg.content and msg.content[0].text.value:
            content = msg.content[0].text.value
            # 필터링 조건: 내용이 비어있지 않고, '..', '...', '전체 지시 사항'을 포함하지 않는 경우에만 UI에 표시
            if content.strip() not in ['', '..', '...'] and '전체 지시 사항' not in content:
                with st.chat_message(msg.role):
                    st.write(content)
    
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")