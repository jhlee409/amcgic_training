import streamlit as st
import time
from datetime import datetime, timedelta
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, initialize_app, storage

# Set page to wide mode
st.set_page_config(page_title="EGD_Dx", layout="wide")

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

    # Firebase Storage에서 MP4 파일의 URL을 검색합니다.
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    blob = bucket.blob("EGD_variation/맨_처음_보세요.mp4")
    video_url = blob.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요: 전체 과정 해설', 
    ]

    # 각 항목에 해당하는 markdown 텍스트 리스트
    markdown_texts = [
        f'<a href="{video_url}" target="_blank">Link 1</a>',
    ]

    # Add custom CSS styles
    st.markdown("""
    <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] > div {
            border: none;
            padding: 5px;
            height: 100%;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:first-child > div {
            height: auto;
        }
    </style>
    """, unsafe_allow_html=True)

    # 제목과 23개 항목 출력
    st.header('제목')
    for idx, item in enumerate(data):
        cols = st.columns([1, 2])  # 2개의 컬럼을 1:1 비율로 생성
        cols[0].write(item)
        if idx < len(markdown_texts):
            cols[1].markdown(markdown_texts[idx], unsafe_allow_html=True)
        else:
            cols[1].write("Link 1, Link 2, Link 3, Link 4, Link 5")

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")