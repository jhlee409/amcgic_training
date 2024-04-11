import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, initialize_app, storage
import sys
import PyQt6
from PyQt6.QtWidgets import QApplication, QFileDialog

# Set page to wide mode
st.set_page_config(page_title="URL_allocation", layout="wide")

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

    # Firebase Storage에서 MP4 파일의 URL을 검색합니다.
    bucket = storage.bucket('amcgi-bulletin.appspot.com')

    # 파일 선택 대화상자 표시
    app = QApplication(sys.argv)
    file_dialog = QFileDialog()
    file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    selected_files = file_dialog.getOpenFileNames()[0]

    # 선택한 파일들에 대한 URL 생성
    file_urls = []
    for file_path in selected_files:
        file_name = file_path.split('/')[-1]
        blob_path = f'AI_EGD_Dx_train/etc/{file_name}'
        blob = bucket.blob(blob_path)
        access_token = blob.generate_signed_url(expiration=3600)
        file_urls.append((file_name, access_token))

    # Streamlit 앱 시작
    st.title('선택한 파일과 URL')

    # 파일 이름과 URL 표시
    for file_name, url in file_urls:
        st.write(f'파일 이름: {file_name}')
        st.write(f'URL: {url}')
        st.write('---')

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")