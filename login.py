import streamlit as st
import requests
import json
import firebase_admin
from firebase_admin import credentials, db
import os

# Firebase 초기화 (아직 초기화되지 않은 경우에만)
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
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["FIREBASE_DATABASE_URL"]
    })

st.set_page_config(page_title="GI_training", layout="wide")

# 제목 및 서브헤딩 설정
st.title("GI training programs")

# 설명 텍스트
with st.expander("**이 프로그램 사용 방법**"):
    st.write("* 로그인이 제대로 안되면 왼쪽 증례 페이지에 접근할 수 없습니다.")
    st.write("* 알려드린 id와 pw로 로그인 하신 후 왼쪽 sidebar에서 원하는 프로그램을 선택하면 그 페이지로 이동합니다.")
    st.write("* 이 프로그램은 울산의대 서울아산병원 이진혁과 의대 관계자 및 다른 서울아산병원 소화기 선생님들의 참여에 의해 제작되었습니다.")
st.divider()

# 사용자 인풋
email = st.text_input("Email")
password = st.text_input("Password", type="password")
name = st.text_input("Name")  # 이름 입력 필드 추가
position = st.selectbox("Position", ["Select Position", "Professor", "Fellow", "Resident", "Student"])  # 직책 선택 필드 추가

# 로그인 버튼
if st.button("Login"):
    try:
        # Streamlit secret에서 Firebase API 키 가져오기
        api_key = st.secrets["FIREBASE_API_KEY"]
        request_ref = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = json.dumps({"email": email, "password": password, "returnSecureToken": True})

        response = requests.post(request_ref, headers=headers, data=data)
        response_data = response.json()

        if response.status_code == 200:
            # Firebase Authentication 성공 후 사용자 정보 가져오기
            user_id = response_data['localId']
            user_ref = db.reference(f'users/{user_id}')
            user_data = user_ref.get()

            if user_data is None:
                # 새 사용자인 경우 정보 저장
                user_ref.set({
                    'email': email,
                    'name': name,
                    'position': position
                })
                user_data = {'name': name, 'position': position}
            
            st.success(f"환영합니다, {user_data.get('name', email)}님! ({user_data.get('position', '직책 미지정')})")
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['user_name'] = user_data.get('name')
            st.session_state['user_position'] = user_data.get('position')
        else:
            st.error(response_data["error"]["message"])
    except Exception as e:
        st.error("An error occurred: " + str(e))

# 로그 아웃 버튼
if "logged_in" in st.session_state and st.session_state['logged_in']:
    
    # 로그인된 사용자 정보 표시
    st.sidebar.write(f"**사용자**: {st.session_state.get('user_name', '이름 없음')}")
    st.sidebar.write(f"**직책**: {st.session_state.get('user_position', '직책 미지정')}")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.success("로그아웃 되었습니다.")
        st.experimental_rerun()

user_email = st.session_state.get('user_email', 'unknown')  # 세션에서 이메일 가져오기