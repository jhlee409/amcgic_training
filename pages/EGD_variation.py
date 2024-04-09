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
        '사진이 흔들려서 찍힘',
        '과도한 retching',
        '진정 시 너무 irritable하다',
        '좌우가 바뀌어 있다(situs inversus)',
        '위안에 음식물이 남아있다',
        '정상 위에서 검사 전과정',
        'STG with Bilroth II reconstruction state애서 검사 전과정',
        'STG with Bilroth I reconstruction state에서 검사 전과정',
        '후두부 접근 시 구역이 심해 후두를 관찰할 수 없다',
        'epiglotis가 닫혀 있어 후부두 전체가 보이는 사진을 찍을 수가 없다',
        '식도가 너무 tortuous 해서 화면 중앙에 놓고 전진하기 힘든다',
        '식도쪽에서 보면 stomach 쪽으로 내려가 있어 z line이 보이지 않는다',
        '궁륭부와 HB 경계부위가 심하게 꺽어져 있어 scope를 밀어도 antrum 쪽으로 진입이 안된다',
        'pyloric ring이 계속 닫혀있고 움직여서 내시경 통과가 어렵다',
        '십이지장 벽에 닿기만 하고, SDA의 위치를 찾지 못하겠다',
        'SDA가 사진 상 우측이 아니라 좌측에 있다.',
        '제2부에서 scope를 당기면 전진하지 않고 그냥 빠지는 양상이다',
        '십이지장 2nd portion인데, ampulla는 보이지 않는데 아무래도 prox 쪽에 있는 것 같다',
        'minor papilla를 AOP로 착각하지 않으려면',
        'antrum GC에 transverse fold가 있어 fold 바로 distal part 부분이 가려져 있다',
        '전정부에서 노브를 up을 했는데도, angle을 관찰할 수 없다',
        '환자의 belcing이 너무 심해 공기가 빠져 fold가 펴지지 않는다'
    ]


   # Add custom CSS styles
    st.markdown("""
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid white;
            padding: 5px;
            text-align: left;
        }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.get('logged_in'):
        # (생략)

        # 제목과 23개 항목 출력
        st.header('제목')
        table_html = """
        <table>
            <thead>
                <tr>
                    <th style="width: 50%;">항목</th>
                    <th style="width: 10%;">Link 1</th>
                    <th style="width: 10%;">Link 2</th>
                    <th style="width: 10%;">Link 3</th>
                    <th style="width: 10%;">Link 4</th>
                    <th style="width: 10%;">Link 5</th>
                </tr>
            </thead>
            <tbody>
        """
        for item in data:
            table_html += f"""
                <tr>
                    <td>{item}</td>
                    <td><a href="https://example.com">Link 1</a></td>
                    <td><a href="https://example.com">Link 2</a></td>
                    <td><a href="https://example.com">Link 3</a></td>
                    <td><a href="https://example.com">Link 4</a></td>
                    <td><a href="https://example.com">Link 5</a></td>
                </tr>
            """
        table_html += """
            </tbody>
        </table>
        """
        
    st.markdown(table_html, unsafe_allow_html=True)
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")