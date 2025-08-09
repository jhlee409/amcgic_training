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
        1. 해당 주제에 대해 여러 증례를 대상으로 해설하는 동양상의 버튼이 오른쪽이 있습니다. 버튼을 눌러 동영상을 시청하세요.
        1. 전체에 대한 안내와 아래에서 나열한, 흔하게 접하는 증례가 포함되어 있으니 이 동영상을 가장 먼저 시청하세요.
        - EGD 사진이 흔들려서 찍히는 경우가 많아요,
        - 환자가 과도한 retching을 해서 검사의 진행이 어려워요,
        - 진정 내시경 시 환자가 너무 irritable해서 검사의 진행이 어려워요,
        - 장기의 좌우가 바뀌어 있다(situs inversus),
        - 위로 진입해 보니, 위안에 음식물이 남아있다,
        - 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요,
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