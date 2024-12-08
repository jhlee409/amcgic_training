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
    
    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요: 전체 과정 해설 A',
        '정상 위에서 Expert의 검사 전과정 B',
        'STG with Bilroth II reconstruction state애서 검사 전과정 C',
        'STG with Bilroth I reconstruction state에서 검사 전과정 D',
        '후두부 접근 시 구역이 심해 후두를 관찰할 수 없다 E',
        'epiglotis가 닫혀서 후부두 전체가 보이는 사진을 찍을 수가 없다 F',
        '식도가 너무 tortuous 해서 화면 중앙에 놓고 전진하기 힘든다 G',
        'z line이 stomach 쪽으로 내려가 있어 z line이 보이지 않는다 H',
        'fundus, HB 경계부위가 심하게 꺽어져 있어, antrum 쪽으로 진입이 안된다 I',
        'pyloric ring이 계속 닫혀있고 움직여서 scope의 통과가 어렵다 J',
        '십이지장 벽에 닿기만 하고, SDA의 위치를 찾지 못하겠다 K',
        'bulb에 들어가 보니, SDA가 사진 상 우측이 아니라 좌측에 있다 L',
        '제2부에서 scope를 당기면 전진해야 하는데, 전진하지 않고 그냥 빠진다 M',
        '십이지장 2nd portion인데, ampulla가 안보이는데 prox 쪽에 있는 것 같다 N',
        'minor papilla를 AOP로 착각하지 않으려면 O',
        'antrum GC에 transverse fold가 있어 그 distal part 부분이 가려져 있다 P',
        '전정부에서 노브를 up을 했는데도, antrum에 붙어서, angle을 관찰할 수 없다 Q',
        '환자의 belcing이 너무 심해 공기가 빠져 fold가 펴지지 않는다 R' 
    ]
    
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
    
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 해당 주제에 대해 여러 증례를 대상으로 해설하는 동양상의 버튼이 오른쪽이 있습니다. 버튼을 눌러 동영상을 시청하세요.")

    # 각 그룹을 8개의 열에 배치
    for letter, videos in grouped_videos.items():
        # 열 생성: 첫 번째 열 너비 5, 나머지 열 너비 1
        cols = st.columns([5, 1, 1, 1, 1, 1, 1, 1])

        # 첫 번째 열에 data 항목 추가
        data_index = ord(letter.upper()) - ord('A')  # letter에 맞는 data 리스트의 인덱스
        if 0 <= data_index < len(data):  # data 인덱스 범위 체크
            with cols[0]:
                st.write(data[data_index])

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