import streamlit as st
import time
from datetime import datetime, timedelta, timezone
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, initialize_app, storage
import requests
import os
import tempfile
import re

# Set page to wide mode
st.set_page_config(page_title="PBL for GIC F2", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()   

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

# 로그 생성을 위한 별도 버킷 (기존 프로젝트 사용)
log_bucket = storage.bucket('amcgi-bulletin.appspot.com')

def create_pbl_log(url, text, description):
    """PBL 버튼 클릭 시 로그 파일을 생성하고 Firebase Storage에 업로드"""
    try:
        # URL에서 숫자 두 자리 추출
        match = re.search(r'pbl-amc-gic-f2-(\d{2})', url)
        if match:
            number = match.group(1)
        else:
            number = "00"  # 기본값
        
        # 로그 파일명 생성
        log_filename = f"PBL_F2_{number}"
        
        # 현재 시간 정보
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # 사용자 정보 (세션에서 가져오기)
        user_name = st.session_state.get('name', 'Unknown')
        user_position = st.session_state.get('position', 'Unknown')
        
        # 로그 내용 생성
        log_content = f"PBL_F2_{number}*{user_name}*{user_position}*{text}*{timestamp}"
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt', encoding='utf-8') as temp_file:
            temp_file.write(log_content)
            temp_file_path = temp_file.name
        
        # Firebase Storage에 업로드 (log 폴더에)
        blob = log_bucket.blob(f"log/{log_filename}")
        blob.upload_from_filename(temp_file_path)
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        
        # 성공 메시지 (사용자에게는 표시하지 않음)
        print(f"PBL 로그 파일 생성 완료: {log_filename}")
        
    except Exception as e:
        print(f"PBL 로그 파일 생성 중 오류 발생: {str(e)}")
        st.error(f"로그 파일 생성 중 오류가 발생했습니다: {str(e)}")


st.header("PBL for GIC F2")

with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.markdown('''
        1. 이 교육 프로그램은 서울아산병원 소화기 상부 전임의 2년차 교육을 위한 고난이도 PBL 훈련 프로그램입니다.
        2. 선택 버튼에 있는 간단한 제목을 보고 누르면 해당 내용이 나타나고 그 내용에서 질문에 대한 선택 버튼을 누르면 하나씩 진행됩니다.
        3. 이 프로그램은 따로 출석이 체크되지 않으나 항상 마지막에 과제가 있습니다. 반드시 한 번은 그 과제를 제출하기 바랍니다.
        ''')

if st.sidebar.button("Logout"):
    logout_time = datetime.now(timezone.utc)
    login_time = st.session_state.get('login_time')
    if login_time:
        if not login_time.tzinfo:
            login_time = login_time.replace(tzinfo=timezone.utc)
        duration = round((logout_time - login_time).total_seconds())
    else:
        duration = 0
    # Supabase 관련 코드 삭제됨
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")

# CSS 스타일 정의
st.markdown("""
<style>
.link-button {
    background-color: #FFE4B5;
    border: 2px solid #FFA500;
    border-radius: 10px;
    padding: 12px;
    margin: 16px 0;
    text-align: center;
    text-decoration: none;
    color: #333;
    font-weight: bold;
    display: block;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    font-size: 0.9em;
    width: 80%;
    margin-left: auto;
    margin-right: auto;
}

.link-button:hover {
    background-color: #FF8C00;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.link-button:active {
    transform: translateY(0);
}
</style>
""", unsafe_allow_html=True)

# 링크 데이터 정의
links_data = [
    # 첫 번째 컬럼 (7개)
    [
        {"url": "https://pbl-amc-gic-f2-01.vercel.app/", "text": "01 stage IV AGC", "description": "stage IV AGC 환자의 검사와 치료"},
        # {"url": "https://pbl-amc-gic-f2-02.vercel.app/", "text": "02 refractory GERD", "description": "refractory GERD 환자의 진단과 치료"},
        # {"url": "https://pbl-amc-gic-f2-03.vercel.app/", "text": "03 GI bleeding", "description": "GI bleeding의 진단과 치료"},
        # {"url": "https://pbl-amc-gic-f2-04.vercel.app/", "text": "04 non curative ESD", "description": "non-curative ESD 정의와 후속 과정정"},
        # {"url": "https://pbl-amc-gic-f2-05.vercel.app/", "text": "05 refractory FD", "description": "refractory FD 환자에서의 약물 치료료"},
        # {"url": "https://pbl-amc-gic-f2-06.vercel.app/", "text": "06 H.pylori 제균치료", "description": "TPL 환자에서의 H. pylori 제균치료"},
        # {"url": "https://pbl-amc-gic-f2-07.vercel.app/", "text": "07 Duodenal NET", "description": "duodenal NET의 진단과 치료료"}
    ],
    # 두 번째 컬럼 (7개)
    [
        # {"url": "https://pbl-amc-gic-f2-08.vercel.app/", "text": "08 Esophageal SET", "description": "large esophageal SET 환자의 management"},
        # {"url": "https://pbl-amc-gic-f2-09.vercel.app/", "text": "09AGC B4", "description": "AGC B4의 진단"},
        # {"url": "https://pbl-amc-gic-f2-10.vercel.app/", "text": "10 Gastric MALT lymphoma", "description": "stage IE1 erosive type gastric MALT lymphoma의 long-term FU"},
        # {"url": "https://pbl-amc-gic-f2-11.vercel.app/", "text": "11 Bayes theorem", "description": "Bayes theorem의 임상적 응용"},
        # {"url": "https://pbl-amc-gic-f2-12.vercel.app/", "text": "12 Gastric polyposis", "description": "Gastric polyposis의 감별진단"},
        # {"url": "https://pbl-amc-gic-f2-13.vercel.app/", "text": "13 Esohageal cancer staging", "description": "Esophageal cancer staging에서 LN metastasis 진단의 중요성"},
        # {"url": "https://pbl-amc-gic-f2-14.vercel.app/", "text": "post gastrectomy dumping syndrome", "description": "post gastrectomy dumping syndrome의 진단과 management"}
    ],
    # 세 번째 컬럼 (7개)
    [
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"},
        # {"url": "#", "text": "PBL", "description": "준비중"}
    ]
]

# 3개 컬럼 생성
col1, col2, col3 = st.columns(3)

# 첫 번째 컬럼에 링크 버튼들 추가
with col1:
    for link in links_data[0]:
        # 로그 생성을 위한 버튼과 링크를 분리
        col_btn, col_link = st.columns([1, 3])
        with col_btn:
            if st.button("📝", key=f"log_{link['text']}", help="로그 생성"):
                create_pbl_log(link['url'], link['text'], link['description'])
                st.success("로그 생성 완료!")
        with col_link:
            st.link_button(f"**{link['text']}**\n{link['description']}", url=link['url'])

# 두 번째 컬럼에 링크 버튼들 추가
with col2:
    for link in links_data[1]:
        # 로그 생성을 위한 버튼과 링크를 분리
        col_btn, col_link = st.columns([1, 3])
        with col_btn:
            if st.button("📝", key=f"log_{link['text']}", help="로그 생성"):
                create_pbl_log(link['url'], link['text'], link['description'])
                st.success("로그 생성 완료!")
        with col_link:
            st.link_button(f"**{link['text']}**\n{link['description']}", url=link['url'])

# 세 번째 컬럼에 링크 버튼들 추가
with col3:
    for link in links_data[2]:
        # 로그 생성을 위한 버튼과 링크를 분리
        col_btn, col_link = st.columns([1, 3])
        with col_btn:
            if st.button("📝", key=f"log_{link['text']}", help="로그 생성"):
                create_pbl_log(link['url'], link['text'], link['description'])
                st.success("로그 생성 완료!")
        with col_link:
            st.link_button(f"**{link['text']}**\n{link['description']}", url=link['url'])