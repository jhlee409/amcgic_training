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

    blob_a1 = bucket.blob("EGD_variation/맨_처음_보세요.mp4")
    video_url_a1 = blob_a1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_b1 = bucket.blob("EGD_variation/B1.mp4")
    video_url_b1 = blob_b1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_b2 = bucket.blob("EGD_variation/B2.mp4")
    video_url_b2 = blob_b2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_c1 = bucket.blob("EGD_variation/C1.mp4")
    video_url_c1 = blob_c1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_c2 = bucket.blob("EGD_variation/C2.mp4")
    video_url_c2 = blob_c2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')


    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요: 전체 과정 해설',
        '- EGD 사진이 흔들려서 찍히는 경우가 많아요',
        '- 환자가 과도한 retching을 해서 검사의 진행이 어려워요',
        '- 진정 내시경 시 환자가 너무 irritable해서 검사의 진행이 어려워요',
        '- 장기의 좌우가 바뀌어 있다(situs inversus)',
        '- 위로 진입해 보니, 위안에 음식물이 남아있다',
        '정상 위에서 Expert의 검사 전과정',
        'STG with Bilroth II reconstruction state애서 검사 전과정',
        'STG with Bilroth I reconstruction state에서 검사 전과정',
        '후두부 접근 시 구역이 심해 후두를 관찰할 수 없다',
        'epiglotis가 닫혀서 후부두 전체가 보이는 사진을 찍을 수가 없다',
        '식도가 너무 tortuous 해서 화면 중앙에 놓고 전진하기 힘든다',
        'z line이 stomach 쪽으로 내려가 있어 z line이 보이지 않는다',
        'fundus, HB 경계부위가 심하게 꺽어져 있어, antrum 쪽으로 진입이 안된다',
        'pyloric ring이 계속 닫혀있고 움직여서 scope의 통과가 어렵다',
        '십이지장 벽에 닿기만 하고, SDA의 위치를 찾지 못하겠다',
        'bulb에 들어가 보니, SDA가 사진 상 우측이 아니라 좌측에 있다.',
        '제2부에서 scope를 당기면 전진해야 하는데, 전진하지 않고 그냥 빠진다',
        '십이지장 2nd portion인데, ampulla가 안보이는데 prox 쪽에 있는 것 같다',
        'minor papilla를 AOP로 착각하지 않으려면',
        'antrum GC에 transverse fold가 있어 그 distal part 부분이 가려져 있다',
        '전정부에서 노브를 up을 했는데도, antrum에 붙어서, angle을 관찰할 수 없다',
        '환자의 belcing이 너무 심해 공기가 빠져 fold가 펴지지 않는다' 
    ]

    # 각 항목에 해당하는 markdown 텍스트 리스트
    markdown_texts = [
        f'<a href="{video_url_a1}" target="_blank">Link 1</a>',
        '-',
        '-',
        '-',
        '-',
        '-',
        f'<a href="{video_url_b1}" target="_blank">Link 1</a>, <a href="{video_url_b2}" target="_blank">Link 1</a>', #B
        f'<a href="{video_url_c1}" target="_blank">Link 1</a>, <a href="{video_url_c2}" target="_blank">Link 1</a>', #C
        f'<a href="https://youtu.be/SrETsnKCVfA" target="_blank">Link 1</a>, <a href="https://youtu.be/PGHM47c3EW4" target="_blank">Link 2</a>', #D
        f'<a href="https://youtu.be/VG2zdExpSzQ" target="_blank">Link 1</a>, <a href="https://youtu.be/Li3BDCeXjZI" target="_blank">Link 2</a>, <a href="https://youtu.be/pSUMTz0cNbk" target="_blank">Link 3</a>, <a href="https://youtu.be/6vLfB_B7mpE" target="_blank">Link 4</a>', #E
        f'<a href="https://youtu.be/Bra3SsDhA00" target="_blank">Link 1</a>, <a href="https://youtu.be/g0WppC-LnXM" target="_blank">Link 2</a>, <a href="https://youtu.be/U_PvOSuRWIw" target="_blank">Link 3</a>', #F
        f'<a href="https://youtu.be/Rgqj5d1HCXs" target="_blank">Link 1</a>', #G
        f'<a href="https://youtu.be/iHUXGo1lEcw" target="_blank">Link 1</a>, <a href="https://youtu.be/o9XbvVpv4I4" target="_blank">Link 2</a>', #H
        f'<a href="https://youtu.be/3I0zq0FEKLU" target="_blank">Link 1</a>, <a href="https://youtu.be/KFRYOBTgHOE" target="_blank">Link 2</a>', #I
        f'<a href="https://youtu.be/5Hxo44wUQkQ" target="_blank">Link 1</a>, <a href="https://youtu.be/iUAbnLxuZcQ" target="_blank">Link 2</a>, <a href="https://youtu.be/YXOoFj5CFjs" target="_blank">Link 3</a>, <a href="https://youtu.be/GGtzY-5vBFM" target="_blank">Link 4</a>, <a href="https://youtu.be/J1jKzg3keHQ" target="_blank">Link 5</a>', #J
        f'<a href="https://youtu.be/-q9-hOskzmI" target="_blank">Link 1</a>', #K
        f'<a href="https://youtu.be/0-SSID0IpbE" target="_blank">Link 1</a>', #L
        f'<a href="https://youtu.be/ObS_-X4k_sg" target="_blank">Link 1</a>', #M
        f'<a href="https://youtu.be/UDCvHPHOwvI" target="_blank">Link 1</a>, <a href="https://youtu.be/AQC18nM8A-0" target="_blank">Link 2</a>, <a href="https://youtu.be/gji_qCaA0cU" target="_blank">Link 3</a>', #N
        f'<a href="https://youtu.be/Xe5J-YygMNo" target="_blank">Link 1</a>, <a href="https://youtu.be/gOMYH1e0sZc" target="_blank">Link 2</a>, <a href="https://youtu.be/ogkpilkuFjs" target="_blank">Link 3</a>', #O
        f'<a href="https://youtu.be/DObihllXWVs" target="_blank">Link 1</a>, <a href="https://youtu.be/5v8zYWOG764" target="_blank">Link 2</a>', #P
        f'<a href="https://youtu.be/RtHnrNNkFlE" target="_blank">Link 1</a>, <a href="https://youtu.be/57-LppXcyKU" target="_blank">Link 2</a>, <a href="https://youtu.be/0UuR4NK_f9Y" target="_blank">Link 3</a>', #Q
        f'<a href="https://youtu.be/PKBsWQdVydg" target="_blank">Link 1</a>, <a href="https://youtu.be/MeFMTwUceWI" target="_blank">Link 2</a>, <a href="https://youtu.be/hDVBCz6hiaY" target="_blank">Link 3</a>', #R
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