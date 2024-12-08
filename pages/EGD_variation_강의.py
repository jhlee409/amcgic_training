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
st.set_page_config(page_title="EGD_Varation", layout="wide")


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
    
# Streamlit 세션 상태 초기화
if "video_states" not in st.session_state:
    st.session_state.video_states = {}

# 동영상 파일 목록 가져오기 함수
def get_video_files_from_folder(bucket, folder_path):
    return [blob.name for blob in bucket.list_blobs(prefix=folder_path) if blob.name.endswith('.mp4')]

# 동영상 파일 목록 가져오기 함수
def get_video_files_from_folder(bucket, folder_path):
    return [blob.name for blob in bucket.list_blobs(prefix=folder_path) if blob.name.endswith('.mp4')]

if st.session_state.get('logged_in'):

    # Firebase 초기화
    if not firebase_admin._apps:
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

    # Firebase Storage bucket reference
    bucket = storage.bucket('amcgi-bulletin.appspot.com')

    # 동영상 목록 가져오기
    folder_path = "EGD_variation/"
    video_files = [blob.name for blob in bucket.list_blobs(prefix=folder_path) if blob.name.endswith('.mp4')]

    st.header("EGD Variation Video Player")
    st.write("아래 버튼을 눌러 동영상을 시청하세요:")

    for video_file in video_files:
        video_name = video_file.replace(folder_path, "")  # Remove folder path for display

        # 각 동영상의 상태 초기화
        if video_name not in st.session_state.video_states:
            st.session_state.video_states[video_name] = False

        # 버튼 생성 및 클릭 처리
        if st.button(f"Play/Close {video_name}"):
            # 상태 반전
            st.session_state.video_states[video_name] = not st.session_state.video_states[video_name]
            


        # 동영상 재생 창
        if st.session_state.video_states[video_name]:
            blob = bucket.blob(video_file)
            video_url = blob.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
            st.video(video_url, format="video/mp4")
            
            # CSS 스타일 적용
            st.markdown(
                """
                <style>
                .stVideo > video {
                    width: 500px;
                    height: auto; /* 세로 비율 유지 */
                }
                </style>
                """,
                unsafe_allow_html=True
                )

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")