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
        '이상하게 사진이 흔들려서 찍힌다',
        '환자가 retching을 과도하게 한다',
        '환자가 진정 내시경 도중 너무 irritable 해서 검사를 더 이상 진행할 수 없을 정도이다',
        '좌우가 바뀌어 있다(situs inversus)',
        '위안에 음식물이 남아있다',
        '정상 위에서 검사 전과정',
        'distal gastrectomy with Bilroth II reconstruction state애서 검사 전과정',
        'distal gastrectomy with Bilroth I reconstruction state에서 검사 전과정',
        '후두부 접근 시 구역이 심해 후두를 관찰할 수 없다',
        'epiglotis가 닫혀 있어 후부두 전체가 보이는 사진을 찍을 수가 없다',
        '식도가 너무 tortuous 해서 화면 중앙에 놓고 전진하기 힘든다',
        '식도쪽에서 보면 stomach 쪽으로 들어가 있어 z line이 보이지 않는다',
        '궁륭부와 HB 경계부위가 심하게 꺽어져 있어 scope를 밀어도 antrum 쪽으로 접근이 안된다',
        'pyloric ring이 계속 닫혀있고 움직여서 내시경 통과가 어렵다',
        '십이지장 벽에 막히기만 하고 SDA의 위치를 찾지 못하겠다',
        'SDA가 사진 상 우측이 아니라 좌측에 있다.',
        '제2부에서 scope를 당기면 전진하지 않고 그냥 빠지는 양상이다',
        '분명 2nd portion인데 ampulla는 보이지 않는데 아무래도 prox 쪽에 있는 것 같다',
        'minor papilla를 AOP로 착각하지 않으려면',
        'antrum GC에 transverse fold가 있어 fold 바로 distal part 부분이 가려져 있다',
        '노브를 up을 했을 때  내시경 선단이 angle에서 떨어지지 않고 붙어서 angle을 관찰할 수 없다',
        '환자의 belcing이 너무 심해 공기가 빠져 fold가 펴지지 않은 상태이다'
    ]

    # 제목과 23개 항목 출력
    st.header('제목')
    for item in data:
        cols = st.columns([5, 1, 1, 1, 1, 1])  # 첫 번째 컬럼의 가로 길이를 3으로, 나머지 컬럼은 1로 설정
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