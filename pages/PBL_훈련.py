import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timezone, timedelta
import requests

# Set page to wide mode
st.set_page_config(page_title="PBL", page_icon=":robot_face:", layout="wide")

if st.session_state.get('logged_in'):
    
    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'displayed_images' not in st.session_state:
        st.session_state['displayed_images'] = []

    # Initialize prompt variable
    prompt = ""

    client = OpenAI()

    # Assistant ID 설정
    assistant_id = "asst_J7yYtxnWNqVxRJkQjMHZzOGJ"  # PBL assistant

    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    # thread_id가 없으면 새로 생성
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

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
        # 이전 대화기록 삭제 버튼
        if st.sidebar.button("이전 대화기록 삭제"):
            # 새로운 thread 생성
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
            # 이미지 기록 삭제
            st.session_state.displayed_images = []
            st.rerun()

        # Streamlit Sidebar with Dropdown for file selection
        case_directory = "PBL/cases/"
        case_file_list = list_files('amcgi-bulletin.appspot.com', case_directory)
        previous_case = st.session_state.get('previous_case', None)
        selected_case_file = st.sidebar.selectbox("증례 파일을 선택하세요.", case_file_list)
        
        # case가 변경되었는지 확인
        if previous_case != selected_case_file:
            st.session_state['previous_case'] = selected_case_file
            # 새로운 thread 생성
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id
            # 이미지 기록 삭제
            st.session_state.displayed_images = []
            st.rerun()

        # Read content of the selected case file and store in prompt variable
        if selected_case_file:
            # assistant_id 설정 및 메시지 처리
            if selected_case_file == "000.docx":
                assistant_id = None
                st.write("🤖: 왼쪽 메뉴에서 증례 파일을 선택해 주세요.")  # assistant 메시지 출력
            else:
                # 사용자 이메일과 접속 날짜 기록
                user_name = st.session_state.get('user_name', 'unknown')
                user_position = st.session_state.get('user_position', 'unknown')
                position_name = f"{user_position}*{user_name}"  # 직책*이름 형식으로 저장
                
                # 한국 시간대(KST) 설정
                kst = timezone(timedelta(hours=9))
                access_date = datetime.now(kst).strftime("%Y-%m-%d")  # 한국 시간으로 현재 날짜 가져오기

                # 로그 내용을 문자열로 생성
                log_entry = f"User: {position_name}, Access Date: {access_date}, Menu: {selected_case_file}\n"

                # '.docx' 확장자를 제거한 파일 이름
                case_file_without_extension = selected_case_file.replace('.docx', '')

                # Firebase Storage에 로그 파일 업로드
                bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
                log_blob = bucket.blob(f'log_PBL/{user_position}*{user_name}*{case_file_without_extension}')  # 로그 파일 경로 설정
                log_blob.upload_from_string(log_entry, content_type='text/plain')  # 문자열로 업로드


                # assistant_id 설정
                if selected_case_file == "PBL_amc_01.docx":
                    assistant_id = "asst_MPsBiEOCzmgElfGwHf757F1b"
                elif selected_case_file == "PBL_amc_02.docx":
                    assistant_id = "asst_DUMZeiSK1m3hYbFqb6OoNbwa"
                else:
                    assistant_id = None  # 다른 경우에 대한 기본값 설정

        # Display Form Title
        main_container.subheader("AMC GI 상부 전임의 2년차 대상 PBL 훈련 챗봇&emsp;&emsp;v 1.0")
        with main_container.expander("원활한 이용을 위해, 반드시 먼저 여길 눌러서 사용방법을 읽어 주세요."):
            st.write("- 처음에는 왼쪽 sidebar에서 증례 파일을 선택해 주세요.")
            st.write("- case가 준비되면 맨 처음은 입력창에 '로딩'을 입력하세요. 관련 자료를 로딩해야 하는데, 좀 오래 걸립니다 ^^;")
            st.write("- 처음부터 이전 대화가 많이 쌓여 있으면, 왼쪽에 있는 '이전 대화기록 삭제버튼'을 눌러 청소하세요.")
            st.write("- 이미지를 보여달라고 할 때, 번호와 이름을 copy and paste 해서 입력해 주어야 합니다. 아니면 엉뚱한 이미지를 보여 줄 수 있습니다.")
            st.write("- 잘못된 이미지를 보여주면, 다시 보여달라고 하면 제대로 보여줍니다.")
            st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")
           
        # Manage thread id
        thread_id = st.session_state.thread_id

        # 초기 프롬프트 전송
        message = client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="assistant",
            content="준비되었습니다."
            )


    # col1과 col2 아래에 입력창 추가
    input_container = st.container()
    with input_container:
        user_input = st.chat_input("입력창입니다. 선생님의 message를 여기에 입력하고 엔터를 치세요")
    
    # 사용자 입력 처리
    if user_input:
        # 사용자 메시지 전송
        message = client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )
        
        # 실행
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id,
        )
        
        with st.spinner('열일 중...'):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

    #while문을 빠져나왔다는 것은 완료됐다는 것이니 메세지 불러오기
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )

    # 메시지 표시
    thread_messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id, 
        order="asc"
    )

    st.sidebar.divider()

    # Clear button in the sidebar
    if st.sidebar.button('이전 대화기록 삭제 버튼'):
        # Reset the prompt, create a new thread, and clear the docx_file and messages
        prompt = []
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state['messages'] = []
        
        # 메시지 내용 초기화
        for msg in thread_messages.data:
            for content in msg.content:
                if hasattr(content, 'text'):
                    content.text.value = ""
        
        # Clear the message box in col2
        st.session_state.message_box = ""
        message_container.markdown("", unsafe_allow_html=True)

    # 이미지 처리를 위한 세션 상태 초기화
    if 'displayed_images' not in st.session_state:
        st.session_state.displayed_images = []

    # assistant 메시지를 메시지 창에 추가
    thread_messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id, 
        order="desc",
        limit=1
    )

    if thread_messages.data:
        latest_message = thread_messages.data[0]
        if latest_message.content:
            for content in latest_message.content:
                # 텍스트 처리
                if hasattr(content, 'text'):
                    text_content = content.text.value
                    if text_content:
                        if latest_message.role == "assistant":
                            st.session_state.message_box += f"🤖: {text_content}\n\n"
                # 이미지 처리
                elif hasattr(content, 'image_file'):
                    image_id = content.image_file.file_id
                    image_data = client.files.content(image_id)
                    # 이미지를 세션 상태에 추가
                    st.session_state.displayed_images.append(image_data.content)

    # 저장된 모든 이미지를 세로로 표시
    for idx, img_data in enumerate(st.session_state.displayed_images):
        # 각 이미지를 위한 새로운 컨테이너 생성
        img_container = message_container.container()
        # 이미지를 컨테이너에 추가
        img_container.image(img_data)
        # 이미지 사이에 작은 간격 추가
        message_container.markdown("<br>", unsafe_allow_html=True)

    # 메시지 박스 업데이트
    message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)

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