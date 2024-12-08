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
if "video_visibility" not in st.session_state:
    st.session_state.video_visibility = False
    st.session_state.current_video_url = ""

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

    # 동영상 파일 목록 가져오기
    folder_path = "EGD_variation/"
    video_files = get_video_files_from_folder(bucket, folder_path)

    st.header("EGD Variation Video Player")
    st.write("아래 버튼을 눌러 동영상을 시청하세요:")

    # 동영상 파일별 버튼 생성
    for video_file in video_files:
        video_name = video_file.replace(folder_path, "")  # Remove folder path for display
        if st.button(f"Play {video_name}"):
            # Test: Signed URL 생성 확인
            blob = bucket.blob("EGD_variation/sample_video.mp4")  # 실제 존재하는 동영상 파일 이름으로 테스트
            video_url = blob.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
            st.write(video_url)  # URL 출력

            # 동영상 URL과 가시성 설정
            st.session_state.current_video_url = video_url
            st.session_state.video_visibility = True

    # 동영상 재생 창
    if st.session_state.video_visibility:
        st.write("### 동영상 재생")
        st.video(video_url, format="video/mp4")  # URL이 HTTPS로 시작해야 정상 작동

        # 닫기 버튼
        if st.button("닫기"):
            st.session_state.video_visibility = False


    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")