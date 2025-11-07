import streamlit as st

# 원래 root 디렉토리에 있던 메인 실행화일을 다른 이름을 변경하여 pages 폴더 안으로 이동시키고
# 이 sidebar_page디자인.py 파일을 root 디렉토리에 복사한 후 이전 main 실행 화일의 이름으로 변경해야 한다.

# Create pages
login_page = st.Page("pages/Login_page.py", title="로그인 페이지", icon=":material/domain:")
page_1 = st.Page("pages/01_Dx_EGD_실전_강의.py", title="01_Dx_EGD_실전_강의", icon=":material/domain:")
page_2 = st.Page("pages/02_EGD_variation_강의.py", title="02_EGD_variation_강의", icon=":material/domain:")
page_3 = st.Page("pages/03_EGD_Lesion_Dx_훈련.py", title="03_EGD_Lesion_Dx_훈련", icon=":material/domain:")
page_4 = st.Page("pages/04_Em_EGD_강의.py", title="04_Em_EGD_강의", icon=":material/domain:")
page_5 = st.Page("pages/05_Dx_EUS_강의.py", title="05_Dx_EUS_강의", icon=":material/domain:")
page_6 = st.Page("pages/06_other_lecture.py", title="06_other_lecture", icon=":material/domain:")
page_7 = st.Page("pages/07_AI_patient_Hx_taking_훈련.py", title="07_AI_patient_Hx_taking_훈련", icon=":material/domain:")
page_8 = st.Page("pages/08_PBL_for_GIC_F2.py", title="08_PBL_for_GIC_F2", icon=":material/domain:")

# 로그인 상태 및 사용자 position 확인
is_logged_in = st.session_state.get('logged_in', False)
user_position = st.session_state.get('position', '')

# 허용된 position 목록 (대소문자 구분 없이 비교)
# Login_page.py에서 "Staff", "F1", "F2", "R3", "Student"로 저장됨
allowed_positions = ['Staff', 'F2', 'F1', 'R3', 'Student', 'staff', 'student']  # 대소문자 모두 포함
is_authorized = False
if user_position:
    # 대소문자 구분 없이 비교
    user_pos_lower = user_position.lower().strip()
    allowed_positions_lower = [pos.lower().strip() for pos in allowed_positions]
    is_authorized = user_pos_lower in allowed_positions_lower

# 로그인 상태와 권한에 따라 페이지 목록 구성
# 기본적으로 보이는 페이지들
endoscopy_pages = [page_2, page_3, page_4, page_6]
clinical_pages = [page_7]

# 로그인했고 권한이 있는 경우에만 특정 페이지 추가
if is_logged_in and is_authorized:
    endoscopy_pages = [page_1, page_2, page_3, page_4, page_5, page_6]
    clinical_pages = [page_7, page_8]

# 디버깅용 - 실제 값 확인 (필요시 주석 해제)
# st.sidebar.write(f"Debug - logged_in: {is_logged_in}")
# st.sidebar.write(f"Debug - position: {user_position}")
# st.sidebar.write(f"Debug - is_authorized: {is_authorized}")
# st.sidebar.write(f"Debug - endoscopy_pages count: {len(endoscopy_pages)}")
# st.sidebar.write(f"Debug - clinical_pages count: {len(clinical_pages)}")

# Set up navigation with sections
pg = st.navigation(
    {
        "로그인 페이지": [login_page],
        "Endoscopy": endoscopy_pages, 
        "Clinical": clinical_pages
    }
)

# Set default page configuration
st.set_page_config(
    page_title="AMC GIC Training",
    page_icon="🤖",
)

# Run the selected page
pg.run() 