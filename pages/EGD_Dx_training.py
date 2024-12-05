import streamlit as st
import pandas as pd
import io
import firebase_admin
from firebase_admin import credentials, storage
import datetime

# Set page to wide mode
st.set_page_config(page_title="EGD_Dx", layout="wide")

if st.session_state.get('logged_in'):

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

    # Display Form Title
    st.subheader("EGD_Dx_training")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 가장 먼저 왼쪽 sidebar에서 F1용인지 F2용인지를 선택합니다.")
        st.write("- 그 아래에서 EGD 사진을 선택해서 업로드 하세요. 다음은 질문이 나옵니다. 잘 생각해 보고 결론이 났으면 왼쪽 sidebar에서 '진행' 버튼을 눌러 답과 설명을 보세요.")
        st.write("- 정리: 가 나오면 증례가 종결된 것입니다. 다음 증례를 위해 초기화를 하거나, 로그아웃을 하세요.")

    # EGD_Dx_training 항목 선택
    selected_item = st.sidebar.selectbox("EGD_Dx_training 항목을 선택하세요", ["항목1", "항목2", "항목3"])  # 항목 목록을 적절히 수정하세요

    if selected_item:
        # 사용자 이메일과 접속 날짜 기록
        user_email = st.session_state.get('user_email', 'unknown')  # 세션에서 이메일 가져오기
        access_date = datetime.datetime.now().strftime("%Y-%m-%d")  # 현재 날짜 가져오기 (시간 제외)
        
        # 데이터프레임 생성
        df = pd.DataFrame({
            'Email': [user_email],
            'Access Date': [access_date]
        })
        
        # 엑셀 파일로 변환
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Access Log')
        
        # Firebase Storage에 엑셀 파일 업로드
        bucket = storage.bucket('amcgi-bulletin.appspot.com')  # Firebase Storage 버킷 참조
        log_blob = bucket.blob(f'logs/access_log_{access_date}.xlsx')  # 로그 파일 경로 설정
        log_blob.upload_from_file(excel_buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')  # 문자열로 업로드

    st.sidebar.divider()

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 