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

# Set page to wide mode
st.set_page_config(page_title="PBL for GIC F2", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()   

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
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"}
    ],
    # 두 번째 컬럼 (7개)
    [
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"}
    ],
    # 세 번째 컬럼 (7개)
    [
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"},
        {"url": "#", "text": "PBL", "description": "준비중"}
    ]
]

# 3개 컬럼 생성
col1, col2, col3 = st.columns(3)

# 첫 번째 컬럼에 링크 버튼들 추가
with col1:
    for link in links_data[0]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)

# 두 번째 컬럼에 링크 버튼들 추가
with col2:
    for link in links_data[1]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)

# 세 번째 컬럼에 링크 버튼들 추가
with col3:
    for link in links_data[2]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)