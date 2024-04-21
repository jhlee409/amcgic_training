import streamlit as st
import time
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage

# 동영상 재생을 위한 라이브러리 추가
import os
import tempfile

# Set page to wide mode
st.set_page_config(page_title="EGD_Hemostasis_training", layout="wide")

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
        
    folder_selection = st.sidebar.radio("Select Folder", ["초기화", "esophagus", "stomach_1", "stomach_2", "duodenum"])

    if folder_selection == "초기화":
        directory_thumbnails = "EGD_Hemostasis_training/default/thumbnails/"  # 추가: 초기화 시 비디오 디렉토리 설정
        #st.experimental_rerun()
    
    elif folder_selection == "esophagus":
        directory_thumbnails = "EGD_Hemostasis_training/esophagus/thumbnails/"  # 추가: esophagus 폴더의 비디오 디렉토리
    elif folder_selection == "stomach_1":
        directory_thumbnails = "EGD_Hemostasis_training/stomach_1/thumbnails/"  # 추가: stomach_1 폴더의 비디오 디렉토리
    elif folder_selection == "stomach_2":
        directory_thumbnails = "EGD_Hemostasis_training/stomach_2/thumbnails/"  # 추가: stomach_2 폴더의 비디오 디렉토리
    else:
        directory_thumbnails = "EGD_Hemostasis_training/duodenum/thumbnails/"  # 추가: duodenum 폴더의 비디오 디렉토리

    st.sidebar.divider()

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

    # 추가: 동영상 파일 리스트 가져오기
    video_list = list_files('amcgi-bulletin.appspot.com', directory_thumbnails)

    # 추가: 동영상 파일 선택 드롭다운 메뉴
    selected_video = st.sidebar.selectbox("동영상 선택", video_list)
    
    if selected_video:
        video_path = directory_thumbnails + selected_video
        
        try:
        # Firebase Storage에서 동영상 파일 다운로드
            bucket = storage.bucket('amcgi-bulletin.appspot.com')
            blob = bucket.blob(video_path)
            
            # 파일을 바이트로 읽어들임
            video_bytes = blob.download_as_bytes()
            
            # 동영상 재생
            st.video(video_bytes, format='video/mp4', start_time=0)
        except Exception as e:
            st.error(f"Error loading video: {str(e)}")

      # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감
     
else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")