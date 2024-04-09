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

    blob_d1 = bucket.blob("EGD_variation/D1.mp4")
    video_url_d1 = blob_d1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_d2 = bucket.blob("EGD_variation/D2.mp4")
    video_url_d2 = blob_d2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_e1 = bucket.blob("EGD_variation/E1.mp4")
    video_url_e1 = blob_e1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_e2 = bucket.blob("EGD_variation/E2.mp4")
    video_url_e2 = blob_e2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_e3 = bucket.blob("EGD_variation/E3.mp4")
    video_url_e3 = blob_e3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_e4 = bucket.blob("EGD_variation/E4.mp4")
    video_url_e4 = blob_e4.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_f1 = bucket.blob("EGD_variation/F1.mp4")
    video_url_f1 = blob_f1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_f2 = bucket.blob("EGD_variation/F2.mp4")
    video_url_f2 = blob_f2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_f3 = bucket.blob("EGD_variation/F3.mp4")
    video_url_f3 = blob_f3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_g1 = bucket.blob("EGD_variation/G1.mp4")
    video_url_g1 = blob_g1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_h1 = bucket.blob("EGD_variation/H1.mp4")
    video_url_h1 = blob_h1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_h2 = bucket.blob("EGD_variation/H2.mp4")
    video_url_h2 = blob_h2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_i1 = bucket.blob("EGD_variation/I1.mp4")
    video_url_i1 = blob_i1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_i2 = bucket.blob("EGD_variation/I2.mp4")
    video_url_i2 = blob_i2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_j1 = bucket.blob("EGD_variation/J1.mp4")
    video_url_j1 = blob_j1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_j2 = bucket.blob("EGD_variation/J2.mp4")
    video_url_j2 = blob_j2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_j3 = bucket.blob("EGD_variation/J3.mp4")
    video_url_j3 = blob_j3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_j4 = bucket.blob("EGD_variation/J4.mp4")
    video_url_j4 = blob_j4.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_j5 = bucket.blob("EGD_variation/J5.mp4")
    video_url_j5 = blob_j5.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_k1 = bucket.blob("EGD_variation/K1.mp4")
    video_url_k1 = blob_k1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_l1 = bucket.blob("EGD_variation/L1.mp4")
    video_url_l1 = blob_l1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_m1 = bucket.blob("EGD_variation/M1.mp4")
    video_url_m1 = blob_m1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_n1 = bucket.blob("EGD_variation/N1.mp4")
    video_url_n1 = blob_n1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_n2 = bucket.blob("EGD_variation/N2.mp4")
    video_url_n2 = blob_n2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_n3 = bucket.blob("EGD_variation/N3.mp4")
    video_url_n3 = blob_n3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_o1 = bucket.blob("EGD_variation/O1.mp4")
    video_url_o1 = blob_o1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_o2 = bucket.blob("EGD_variation/O2.mp4")
    video_url_o2 = blob_o2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_o3 = bucket.blob("EGD_variation/O3.mp4")
    video_url_o3 = blob_o3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_p1 = bucket.blob("EGD_variation/P1.mp4")
    video_url_p1 = blob_p1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_p2 = bucket.blob("EGD_variation/P2.mp4")
    video_url_p2 = blob_p2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_q1 = bucket.blob("EGD_variation/Q1.mp4")
    video_url_q1 = blob_q1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_q2 = bucket.blob("EGD_variation/Q2.mp4")
    video_url_q2 = blob_q2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_q3 = bucket.blob("EGD_variation/Q3.mp4")
    video_url_q3 = blob_q3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')

    blob_r1 = bucket.blob("EGD_variation/R1.mp4")
    video_url_r1 = blob_r1.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_r2 = bucket.blob("EGD_variation/R2.mp4")
    video_url_r2 = blob_r2.generate_signed_url(expiration=timedelta(seconds=300), method='GET')
    blob_r3 = bucket.blob("EGD_variation/R3.mp4")
    video_url_r3 = blob_r3.generate_signed_url(expiration=timedelta(seconds=300), method='GET')





    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요: 전체 과정 해설 A',
        '- EGD 사진이 흔들려서 찍히는 경우가 많아요',
        '- 환자가 과도한 retching을 해서 검사의 진행이 어려워요',
        '- 진정 내시경 시 환자가 너무 irritable해서 검사의 진행이 어려워요',
        '- 장기의 좌우가 바뀌어 있다(situs inversus)',
        '- 위로 진입해 보니, 위안에 음식물이 남아있다',
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
        f'<a href="{video_url_d1}" target="_blank">Link 1</a>, <a href="{video_url_d2}" target="_blank">Link 1</a>', #D
        f'<a href="{video_url_e1}" target="_blank">Link 1</a>, <a href="{video_url_e2}" target="_blank">Link 1</a>, <a href="{video_url_e3}" target="_blank">Link 1</a>, <a href="{video_url_e4}" target="_blank">Link 1</a>', #E
        f'<a href="{video_url_f1}" target="_blank">Link 1</a>, <a href="{video_url_f2}" target="_blank">Link 1</a>, <a href="{video_url_f3}" target="_blank">Link 1</a>', #F
        f'<a href="{video_url_g1}" target="_blank">Link 1</a>', #G
        f'<a href="{video_url_h1}" target="_blank">Link 1</a>, <a href="{video_url_h2}" target="_blank">Link 1</a>', #H
        f'<a href="{video_url_i1}" target="_blank">Link 1</a>, <a href="{video_url_i2}" target="_blank">Link 1</a>', #I
        f'<a href="{video_url_j1}" target="_blank">Link 1</a>, <a href="{video_url_j2}" target="_blank">Link 1</a>, <a href="{video_url_j3}" target="_blank">Link 1</a>, <a href="{video_url_j4}" target="_blank">Link 1</a>, <a href="{video_url_j5}" target="_blank">Link 1</a>', #J
        f'<a href="{video_url_k1}" target="_blank">Link 1</a>', #K
        f'<a href="{video_url_l1}" target="_blank">Link 1</a>', #L
        f'<a href="{video_url_m1}" target="_blank">Link 1</a>', #M
        f'<a href="{video_url_n1}" target="_blank">Link 1</a>, <a href="{video_url_n2}" target="_blank">Link 1</a>, <a href="{video_url_n3}" target="_blank">Link 1</a>', #N
        f'<a href="{video_url_o1}" target="_blank">Link 1</a>, <a href="{video_url_o2}" target="_blank">Link 1</a>, <a href="{video_url_o3}" target="_blank">Link 1</a>', #O
        f'<a href="{video_url_p1}" target="_blank">Link 1</a>, <a href="{video_url_p2}" target="_blank">Link 1</a>', #P
        f'<a href="{video_url_q1}" target="_blank">Link 1</a>, <a href="{video_url_q2}" target="_blank">Link 1</a>, <a href="{video_url_q3}" target="_blank">Link 1</a>', #Q
        f'<a href="{video_url_r1}" target="_blank">Link 1</a>, <a href="{video_url_r2}" target="_blank">Link 1</a>, <a href="{video_url_r3}" target="_blank">Link 1</a>', #R
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