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
    
    st.session_state.video_states = {}
    # Streamlit 세션 상태 초기화
    if "video_states" not in st.session_state:
        st.session_state.video_states = {}
        
    # 동영상 파일 목록 가져오기 함수
    def get_video_files_from_folder(bucket, folder_path):
        return [blob.name for blob in bucket.list_blobs(prefix=folder_path) if blob.name.endswith('.mp4')]
    
     # 동영상 목록 가져오기
    folder_path = "EGD_variation/"
    video_files = get_video_files_from_folder(bucket, folder_path)

    # 동영상 이름으로 정렬 및 그룹화
    video_files_sorted = sorted(video_files)
    grouped_videos = {}
    for video in video_files_sorted:
        first_letter = video.replace(folder_path, "")[0].upper()  # 첫 글자 추출
        if first_letter not in grouped_videos:
            grouped_videos[first_letter] = []
        grouped_videos[first_letter].append(video)

    st.header("EGD variation 강의")
    st.write("아래 버튼을 눌러 동영상을 시청하세요:")
    
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 해당 주제에 대해 여러 증례를 대상으로 해설하는 동양상의 버튼이 오른쪽이 있습니다. 버튼을 눌러 동영상을 시청하세요.")
        
    st.sidebar.divider()

    # 각 그룹을 8개의 열에 배치
    for letter, videos in grouped_videos.items():
        # 열 생성: 첫 번째 열 너비 5, 나머지 열 너비 1
        cols = st.columns([5, 1, 1, 1, 1, 1, 1, 1])

        # 두 번째 열부터 버튼 채우기
        for idx, video_file in enumerate(videos):
            if idx < 5:  # 버튼은 최대 5개까지만 표시
                with cols[idx + 1]:  # 두 번째 열부터 버튼 추가
                    video_name = video_file.replace(folder_path, "").replace('.mp4', "")  # 확장자 제거

                    # 각 동영상의 상태 초기화
                    if video_name not in st.session_state.video_states:
                        st.session_state.video_states[video_name] = False

                    # 버튼 생성 및 클릭 처리
                    if st.button(f"{video_name}"):
                        # 상태 반전
                        st.session_state.video_states[video_name] = not st.session_state.video_states[video_name]

                    # 동영상 재생 창
                    if st.session_state.video_states[video_name]:
                        st.session_state.video_states = {}
                        blob = bucket.blob(video_file)
                        video_url = blob.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
                        st.markdown(
                            f"""
                            <div style="display: flex; justify-content: center; align-items: center;">
                                <video controls style="width: 600%; height: auto;">
                                    <source src="{video_url}" type="video/mp4">
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


    # 로그아웃 버튼
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()

else:
    st.error("로그인이 필요합니다.")