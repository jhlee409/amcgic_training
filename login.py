import streamlit as st

# 원래 root 디렉토리에 있던 메인 실행화일을 다른 이름을 변경하여 pages 폴더 안으로 이동시키고
# 이 sidebar_page디자인.py 파일을 root 디렉토리에 복사한 후 이전 main 실행 화일의 이름으로 변경해야 한다.

# Create pages
login_page = st.Page("pages/Login_page.py", title="로그인 페이지", icon=":material/domain:")
page_1 = st.Page("pages/01_Dx_EGD_실전_강의", title="01_Dx_EGD_실전_강의", icon=":material/domain:")
page_2 = st.Page("pages/02_EGD_variation_강의", title="02_EGD_variation_강의", icon=":material/domain:")
page_3 = st.Page("pages/03_EGD_Lesion_Dx_훈련", title="03_EGD_Lesion_Dx_훈련", icon=":material/domain:")
page_4 = st.Page("pages/04_Em_EGD_강의", title="04_Em_EGD_강의", icon=":material/domain:")
page_5 = st.Page("pages/05_Dx_EUS_강의", title="05_Dx_EUS_강의", icon=":material/domain:")
page_6 = st.Page("pages/06_other_lecture", title="06_other_lecture", icon=":material/domain:")
page_7 = st.Page("pages/07_AI_patient_Hx_taking_훈련", title="07_AI_patient_Hx_taking_훈련", icon=":material/domain:")
page_8 = st.Page("pages/08_PBL_for_GIC_F2", title="08_PBL_for_GIC_F2", icon=":material/domain:")


# Set up navigation with sections
pg = st.navigation(
    {
        "로그인 페이지": [login_page],
        "Endoscopy": [page_1, page_2, page_3, page_4, page_5, page_6], 
        "Clinical":  [page_7, page_8]
    }
)

# Set default page configuration
st.set_page_config(
    page_title="AMC GIC Training",
    page_icon="🤖",
)

# Run the selected page
pg.run() 