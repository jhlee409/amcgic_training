import streamlit as st
import pandas as pd

st.set_page_config(page_title="GI_training", layout="wide")

# 제목 및 서브헤딩 설정
st.title("GI training programs")

# 설명 텍스트
with st.expander("**이 프로그램 사용 방법**"):
    st.write("* 로그인이 제대로 안되면 왼쪽 증례 페이지에 접근할 수 없습니다.")
    st.write("* 알려드린 id와 pw로 로그인 하신 후 왼쪽 sidebar에서 원하는 프로그램을 선택하면 그 페이지로 이동합니다.")
    st.write("* 이 프로그램은 울산의대 서울아산병원 이진혁과 의대 관계자 및 다른 서울아산병원 소화기 선생님들의 참여에 의해 제작되었습니다.")
st.divider()

# 로그아웃 버튼 상태 관리
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# 로그인 상태에 따른 UI 표시
if not st.session_state.logged_in:
    # 사용자 ID 및 비밀번호 입력창 설정
    st.subheader("로그인 페이지")
    id = st.text_input("사용자 ID")
    password = st.text_input("비밀번호", type="password")

    # 로그인 버튼 추가
    login_button = st.button('로그인')

    # 로그인 버튼이 클릭되었을 때만 처리
    if login_button:
        # ID 및 비밀번호 확인
        is_login = id == "amcgi" and password == "3986"

        if is_login:
            # 로그인 성공 시 처리
            st.success("로그인에 성공하셨습니다. 이제 왼편의 각 프로그램을 사용하실 수 있습니다.")
            st.session_state.logged_in = True
            st.divider()
        else:
            st.error("로그인 정보가 정확하지 않습니다.")
else:
    # 로그인 성공 시 화면
    st.success("로그인에 성공하셨습니다. 이제 왼편의 각 프로그램을 사용하실 수 있습니다.")
    st.divider()
    
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

    st.write("마지막 수정 날짜 및 수정사항: 2024년 2월 15일; EGD 사진 진단 훈련 프로그램 내용 삭제")