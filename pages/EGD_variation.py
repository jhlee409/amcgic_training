import streamlit as st
import time
from PIL import Image
import docx
import io
from openai import OpenAI

# Set page to wide mode
st.set_page_config(page_title="EGD_Variation", layout="wide")

if st.session_state.get('logged_in'):

    # Initialize prompt variable
    prompt = ""      

    client = OpenAI()

    # Display Form Title
    st.subheader("EGD_Variation")
    with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 먼저 컬럼에서 '가장 먼저 보세요: 전체 과정 해설' 링크를 통해 동영상을 시청합니다..")
        st.write("- 다음 보고 싶은 특정 상황에서의 대처법에 해당하는 동영상 링크를 통해 동영상을 시청합니다.")


    # 23개 항목의 데이터
    data = [
        '가장 먼저 보세요: 전체 과정 해설', 
        '- EGD 사진이 흔들려서 찍히는 경우가 많아요',
        '- 환자가 과도한 retching을 해서 검사의 진행이 어려워요',
        '- 진정 내시경 시 환자가 너무 irritable해서 검사의 진행이 어려워요',
        '- 장기의 좌우가 바뀌어 있다(situs inversus)',
        '- 위로 진입해 보니, 위안에 음식물이 남아있다',
        '- 정상 위에서 Expert의 검사 전과정',
        '- STG with Bilroth II reconstruction state애서 검사 전과정',
        '- STG with Bilroth I reconstruction state에서 검사 전과정',
        '- 후두부 접근 시 구역이 심해 후두를 관찰할 수 없다',
        '- epiglotis가 닫혀서 후부두 전체가 보이는 사진을 찍을 수가 없다',
        '- 식도가 너무 tortuous 해서 화면 중앙에 놓고 전진하기 힘든다',
        '- z line이 stomach 쪽으로 내려가 있어 z line이 보이지 않는다',
        '- fundus, HB 경계부위가 심하게 꺽어져 있어, antrum 쪽으로 진입이 안된다',
        '- pyloric ring이 계속 닫혀있고 움직여서 scope의 통과가 어렵다',
        '- 십이지장 벽에 닿기만 하고, SDA의 위치를 찾지 못하겠다',
        '- bulb에 들어가 보니, SDA가 사진 상 우측이 아니라 좌측에 있다.',
        '- 제2부에서 scope를 당기면 전진해야 하는데, 전진하지 않고 그냥 빠진다',
        '- 십이지장 2nd portion인데, ampulla가 안보이는데 prox 쪽에 있는 것 같다',
        '- minor papilla를 AOP로 착각하지 않으려면',
        '- antrum GC에 transverse fold가 있어 그 distal part 부분이 가려져 있다',
        '- 전정부에서 노브를 up을 했는데도, antrum에 붙어서, angle을 관찰할 수 없다',
        '- 환자의 belcing이 너무 심해 공기가 빠져 fold가 펴지지 않는다'
    ]

    # 각 항목에 해당하는 markdown 텍스트 리스트
    markdown_texts = [
        '<a href="https://youtu.be/Rzbshcwe3ZE" target="_blank">Link 1</a>',
        '<a href="https://www.youtube.com/watch?v=VIDEO_ID_2" target="_blank">Link 1</a>, <a href="https://www.youtube.com/watch?v=VIDEO_ID_2" target="_blank">Link 2</a>',
        '<a href="https://www.youtube.com/watch?v=VIDEO_ID_3" target="_blank">Link 1</a>, <a href="https://www.youtube.com/watch?v=VIDEO_ID_3" target="_blank">Link 2</a>, <a href="https://www.youtube.com/watch?v=VIDEO_ID_3" target="_blank">Link 3</a>',
        # ... 나머지 항목에 해당하는 markdown 텍스트 추가
    ]

    # Add custom CSS styles
    st.markdown("""
    <style>
        div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] > div {
            border: none;
            padding: 5px;
            height: 100%;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"]:first-child > div {
            height: auto;
        }
    </style>
    """, unsafe_allow_html=True)

    # 제목과 23개 항목 출력
    st.header('제목')
    for idx, item in enumerate(data):
        cols = st.columns([1, 2])  # 2개의 컬럼을 1:1 비율로 생성
        cols[0].write(item)
        if idx < len(markdown_texts):
            cols[1].markdown(markdown_texts[idx], unsafe_allow_html=True)
        else:
            cols[1].write("Link 1, Link 2, Link 3, Link 4, Link 5")


    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")