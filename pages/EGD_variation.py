import streamlit as st
import time
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="EGD_Variation", layout="wide")

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

    client = OpenAI()

    # Display Form Title
    st.subheader("EGD_Variation")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 먼저 컬럼에서 '가장 먼저 보세요' 링크를 통해 동영상을 시청합니다..")
        st.write("- 다음 보고 싶은 특정 상황에서의 대처법에 해당하는 동영상 링크를 통해 동영상을 시청합니다.")


    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요', 
        '내시경에서 대장암 진단: 용종의 색상이 붉은 색일때',
        '분화형 선종: 선구조(pit pattern) 관찰이 명확하지 않을때',
        '평탄 융기형 병변(flat elevated lesion)이 관찰될 때',
        '용종 표면에 백태(whitish patch) 관찰될때',
        '직장에서 병변이 관찰될때: 직장암과 선종의 감별',
        '대장암으로 진단되는 소견',
        '대장암 치료 후 추적 관찰시 문합부(anastomosis site)관찰',
        '대장 게실 관찰시',
        '육안 소견상 정상 점막(normal mucosa)처럼 보일때',
        '흑색종(melanosis) 관찰될 때',
        '방사선 직장염(radiation proctitis) 관찰될 때',
        '대장 점막 투명캡(transparent cap)으로 관찰시',
        '장정결제 잔여물 확인시',
        '대장 점막하 종양(submucosal tumor) 관찰될 때',
        '대장 용종 snare polypectomy중 시술시',
        '대장 용종에서 출혈(bleeding) 관찰시',
        '내시경적 점막 절제술(Endoscopic Mucosal Resection) 후 절제면 관찰시',
        '대장 용종 snare polypectomy중 남은 용종이 있을때',
        '대장암에서 동시성 병변 관찰시',
        '대장의 점막하층 박리술(Endoscopic submucosal dissection) 시술 관찰시',
        '대장 내시경 삽입시 힘들때: 내시경 삽입이 잘 안될때',
        '내시경 세척(washing) 관찰시'
    ]

    # 제목과 23개 항목 출력
    st.header('제목')
    for item in data:
        cols = st.columns(6)
        cols[0].write(item)
        for i in range(1, 6):
            cols[i].write('')  # 빈 셀 추가
        
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 