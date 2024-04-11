import streamlit as st
import time
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage  

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
    
# Storage 참조 생성
bucket = storage.bucket('amcgi-bulletin.appspot.com')

# 이미지 파일 경로
image_path = 'etc/image_001.png'

# 파일 참조 생성
blob = bucket.blob(image_path)

# 파일에 대한 액세스 토큰 생성
access_token = blob.generate_signed_url(expiration=3600)

# URL 주소 출력
print(f'이미지 URL: {access_token}')