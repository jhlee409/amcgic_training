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
    padding: 15px;
    margin: 10px 0;
    text-align: center;
    text-decoration: none;
    color: #333;
    font-weight: bold;
    display: block;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        {"url": "https://www.google.com", "text": "구글 검색", "description": "세계 최고의 검색 엔진"},
        {"url": "https://www.youtube.com", "text": "유튜브", "description": "동영상 공유 플랫폼"},
        {"url": "https://www.github.com", "text": "깃허브", "description": "코드 저장소 및 협업 플랫폼"},
        {"url": "https://www.stackoverflow.com", "text": "스택오버플로우", "description": "개발자 질문답변 사이트"},
        {"url": "https://www.wikipedia.org", "text": "위키피디아", "description": "자유 백과사전"},
        {"url": "https://www.reddit.com", "text": "레딧", "description": "온라인 커뮤니티 플랫폼"},
        {"url": "https://www.twitter.com", "text": "트위터", "description": "소셜 미디어 플랫폼"}
    ],
    # 두 번째 컬럼 (7개)
    [
        {"url": "https://www.linkedin.com", "text": "링크드인", "description": "전문가 네트워킹 플랫폼"},
        {"url": "https://www.medium.com", "text": "미디엄", "description": "글쓰기 및 콘텐츠 플랫폼"},
        {"url": "https://www.notion.so", "text": "노션", "description": "생산성 및 협업 도구"},
        {"url": "https://www.figma.com", "text": "피그마", "description": "디자인 및 프로토타이핑 도구"},
        {"url": "https://www.slack.com", "text": "슬랙", "description": "팀 커뮤니케이션 도구"},
        {"url": "https://www.trello.com", "text": "트렐로", "description": "프로젝트 관리 도구"},
        {"url": "https://www.asana.com", "text": "아사나", "description": "작업 관리 및 협업 플랫폼"}
    ],
    # 세 번째 컬럼 (7개)
    [
        {"url": "https://www.dropbox.com", "text": "드롭박스", "description": "클라우드 파일 저장소"},
        {"url": "https://www.zoom.us", "text": "줌", "description": "화상회의 플랫폼"},
        {"url": "https://www.coursera.org", "text": "코세라", "description": "온라인 교육 플랫폼"},
        {"url": "https://www.udemy.com", "text": "유데미", "description": "온라인 강의 플랫폼"},
        {"url": "https://www.khanacademy.org", "text": "칸 아카데미", "description": "무료 교육 리소스"},
        {"url": "https://www.ted.com", "text": "TED", "description": "영감을 주는 강연 플랫폼"},
        {"url": "https://www.duolingo.com", "text": "듀오링고", "description": "언어 학습 앱"}
    ]
]

# 3개 컬럼 생성
col1, col2, col3 = st.columns(3)

# 첫 번째 컬럼에 링크 버튼들 추가
with col1:
    st.subheader("🔍 검색 및 정보")
    for link in links_data[0]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)

# 두 번째 컬럼에 링크 버튼들 추가
with col2:
    st.subheader("💼 업무 및 협업")
    for link in links_data[1]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)

# 세 번째 컬럼에 링크 버튼들 추가
with col3:
    st.subheader("📚 학습 및 교육")
    for link in links_data[2]:
        st.markdown(f"""
        <a href="{link['url']}" target="_blank" class="link-button">
            <strong>{link['text']}</strong><br>
            <small>{link['description']}</small>
        </a>
        """, unsafe_allow_html=True)