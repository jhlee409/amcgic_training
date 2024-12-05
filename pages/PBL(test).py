import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime

# Set page to wide mode
st.set_page_config(page_title="PBL Test", layout="wide")

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

    # Display Form Title
    st.subheader("PBL Test")

    # 라디오 버튼으로 01과 02 선택
    selected_option = st.radio("옵션을 선택하세요:", ["01", "02"])

    # 선택된 어시스턴트 설정
    if selected_option == "01":
        assistant_id = "asst_TSbYs8y40TmTUqwEu9eGSF6w"
    else:
        assistant_id = "기타"  # 02를 선택했을 때의 기본값

    # 선택된 옵션과 어시스턴트 표시
    st.write(f"선택한 옵션: {selected_option}")
    st.write(f"선택된 어시스턴트 ID: {assistant_id}")

    # 대화 시작
    if st.button("대화 시작"):
        prompt = st.text_input("대화 내용을 입력하세요:", "")  # 사용자가 입력한 내용을 받기 위한 텍스트 입력

        if prompt:  # 사용자가 내용을 입력했는지 확인
            # 새로운 thread ID 생성
            thread_response = client.beta.threads.create(
                assistant_id=assistant_id,
                title="New Conversation Thread"  # 필요에 따라 제목을 설정
            )
            thread_id = thread_response.id  # 생성된 thread ID 가져오기

            # 메시지 생성
            message = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )

            # RUN을 돌리는 과정
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

            # 대화 결과 처리 (예: 응답 표시)
            st.write("대화가 시작되었습니다. 새로운 thread ID:", thread_id)

            # 로그 파일 생성
            user_email = st.session_state.get('user_email', 'unknown')  # 세션에서 이메일 가져오기
            access_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)

            # 로그 내용을 문자열로 생성
            log_entry = f"Email: {user_email}, Option: {selected_option}, Access Date: {access_date}\n"

            # Firebase Storage에 로그 파일 업로드
            bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
            log_blob = bucket.blob(f'logs/{user_email}_PBL_{selected_option}_{access_date}.txt')  # 로그 파일 경로 설정
            log_blob.upload_from_string(log_entry, content_type='text/plain')  # 문자열로 업로드

        else:
            st.error("대화 내용을 입력해야 합니다.")  # 대화 내용이 비어있을 경우 오류 메시지 표시

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")
