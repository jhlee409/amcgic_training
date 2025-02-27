import streamlit as st
import os
from PIL import Image
import docx
import io
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime, timedelta, timezone
import requests
import json
import os
import tempfile

# Set page to wide mode
st.set_page_config(page_title="EGD_Hemostasis_lecture", layout="wide")

# 로그인 상태 확인
if "logged_in" not in st.session_state or not st.session_state['logged_in']:
    st.warning('로그인이 필요합니다.')
    st.stop()   

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
st.subheader("EGD_Hemostasis_lecture")
with st.expander(" 필독!!! 먼저 여기를 눌러 사용방법을 확인하세요."):
    st.write("- 가장 먼저 왼쪽 sidebar 선택버튼에서 default는 'Default'입니다. Hemostasis lecture, cases 중 한 가지를 선택합니다.")
    st.write("- 우선 EGD 지혈술의 overview 강의를 시청하고 싶으면, Hemostasis lecture를 선택하고 '진행' 버튼을 누르면 강의 화면이 나타납니다. 클릭해서 시청하세요.")
    st.write("- EGD 지혈술 case를 시청하고 싶으면 cases 버튼을 선택하고 드롭다운 메뉴에서 case를 선택하면 치료전 case 동영상과 질문이 나타납니다.")
    st.write("- 잘 생각해 보고 '진행' 버튼을 누르면 답과 시술 동영상을 볼수있는 동영상 player가 나타납니다.")
    st.write("- 동영상을 클릭해서 보시면 됩니다.")
    st.write("* 이 웹페이지의 출석이 기록됩니다. 끝낼 때는 반드시 좌측 하단 로그아웃 버튼을 눌러서 종결하세요.")
        
def list_files(bucket_name, directory):
    bucket = storage.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=directory)
    return [blob.name[len(directory):] for blob in blobs if blob.name[len(directory):]]

def read_docx(bucket_name, file_name):
    try:
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_name)
        content = blob.download_as_bytes()
        doc = docx.Document(io.BytesIO(content))
        return '\n'.join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"문서를 읽는 중 오류 발생: {str(e)}")
        return ""

folder_selection = st.sidebar.radio("선택 버튼", ["Default", "Hemostasis lecture", "cases"])

directories = {
    "Default": "EGD_Hemostasis_training/default/",
    "Hemostasis lecture": "EGD_Hemostasis_training/lecture/",
    "cases": "EGD_Hemostasis_training/cases/"
}

directory = directories[folder_selection]

# 폴더 선택이 변경되었을 때 상태 초기화
if st.session_state.get('previous_folder_selection') != folder_selection:
    st.session_state.previous_folder_selection = folder_selection
    st.session_state.selected_file = None
    st.session_state.prevideo_url = None
    st.session_state.video_url = None
    # 현재 선택된 폴더의 파일 목록을 가져오기 (mp4 파일만, _main 제외)
    st.session_state.current_file_list = [f for f in list_files('amcgi-bulletin.appspot.com', directory) 
                                        if f.endswith('.mp4') and '_prevideo' not in f]
    st.rerun()

# 현재 폴더의 파일 목록 사용
file_list = st.session_state.get('current_file_list', [])
selected_file = st.sidebar.selectbox("파일 선택", file_list)

if selected_file and selected_file != st.session_state.get('selected_file'):
    st.session_state.selected_file = selected_file
    file_path = directory + selected_file
    base_name = os.path.splitext(selected_file)[0]
    
    bucket = storage.bucket('amcgi-bulletin.appspot.com')
    expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
    
    # prevideo 파일 경로 설정 및 URL 생성
    prevideo_path = directory + base_name + '_prevideo.mp4'
    prevideo_blob = bucket.blob(prevideo_path)
    if prevideo_blob.exists():
        st.session_state.prevideo_url = prevideo_blob.generate_signed_url(expiration=expiration_time, method='GET')
    
    # main 동영상 경로 설정
    st.session_state.main_video_path = file_path
    
    # instruction 파일 처리
    instruction_file = directory + base_name + '.docx'
    st.session_state.instruction_text = read_docx('amcgi-bulletin.appspot.com', instruction_file)
    
    st.rerun()

# 좌우 컨테이너 생성
left_col, right_col = st.columns([2, 4])

# 왼쪽 컨테이너에 첫 번째 동영상과 설명 표시
with left_col:
    if st.session_state.get('prevideo_url'):
        video_html = f"""
            <div style="width: 500px; margin: auto;">
                <video style="width: 100%; height: auto;" controls src="{st.session_state.prevideo_url}">
                    Your browser does not support the video element.
                </video>
            </div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    if st.session_state.get('instruction_text'):
        st.markdown(st.session_state.instruction_text)

# 오른쪽 컨테이너에 '진행' 버튼 클릭 시 나타나는 동영상 표시
with right_col:
    if st.sidebar.button('본강의 시청'):
        if st.session_state.get('main_video_path'):
            blob = storage.bucket('amcgi-bulletin.appspot.com').blob(st.session_state.main_video_path)
            expiration_time = datetime.now(timezone.utc) + timedelta(seconds=1600)
            video_url = blob.generate_signed_url(expiration=expiration_time, method='GET')
            video_html = f"""
                <div style="width: 1100px; margin: auto;">
                    <video style="width: 100%; height: auto;" controls src="{video_url}">
                        Your browser does not support the video element.
                    </video>
                </div>
            """
            st.markdown(video_html, unsafe_allow_html=True)

            # 로그 정보 저장
            base_name = os.path.splitext(selected_file)[0]  # .mp4 제외한 파일 이름
            log_file_name = f"log_EGD_Hemostasis/{st.session_state.get('position')}*{st.session_state.get('name')}*{base_name}"
            log_data = {
                "file_name": selected_file,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            # Firebase에 로그 정보 저장
            blob = storage.bucket('amcgi-bulletin.appspot.com').blob(log_file_name)
            blob.upload_from_string(json.dumps(log_data), content_type='application/json')

if st.sidebar.button("Logout"):
    logout_time = datetime.now(timezone.utc)
    login_time = st.session_state.get('login_time')
    if login_time:
        if not login_time.tzinfo:
            login_time = login_time.replace(tzinfo=timezone.utc)
        duration = round((logout_time - login_time).total_seconds() / 60)
    else:
        duration = 0
    
    logout_data = {
        "position": st.session_state.get('position'),
        "name": st.session_state.get('name'),
        "time": logout_time.isoformat(),
        "event": "logout",
        "duration": duration
    }
    
    requests.post(f"{st.secrets['supabase_url']}/rest/v1/login", headers={
        "Content-Type": "application/json",
        "apikey": st.secrets["supabase_key"],
        "Authorization": f"Bearer {st.secrets['supabase_key']}"
    }, json=logout_data)
    
    try:
        # 현재 시간 가져오기 (초 단위까지)
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        position = st.session_state.get('position', '')
        name = st.session_state.get('name', '')
        
        # Firebase Storage 버킷 가져오기
        bucket = storage.bucket('amcgi-bulletin.appspot.com')
        
        # 로그인 시간 가져오기
        login_timestamp = None
        login_blobs = list(bucket.list_blobs(prefix="log_login/"))
        
        # 현재 사용자의 가장 최근 로그인 찾기
        for blob in sorted(login_blobs, key=lambda x: x.name, reverse=True):
            try:
                # 임시 파일에 다운로드
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    with open(temp_file.name, 'r') as f:
                        content = f.read()
                    os.unlink(temp_file.name)
                
                # 로그 내용 파싱
                parts = content.split('*')
                if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                    login_timestamp = datetime.strptime(parts[3], '%Y-%m-%d %H:%M:%S')
                    # 로그인 파일 찾았으므로 삭제
                    blob.delete()
                    break
            except Exception as e:
                st.error(f"로그인 로그 파일 처리 중 오류 발생: {str(e)}")
        
        # 로그아웃 로그 파일 생성 및 업로드
        log_content = f"{position}*{name}*logout*{now.strftime('%Y-%m-%d %H:%M:%S')}"
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write(log_content)
            temp_file_path = temp_file.name
        
        log_filename = f"log_logout/{timestamp}"
        blob = bucket.blob(log_filename)
        blob.upload_from_filename(temp_file_path)
        
        # 시간 차이 계산 및 duration 로그 생성
        if login_timestamp:
            # login_timestamp에 타임존 정보 추가
            if not login_timestamp.tzinfo:
                login_timestamp = login_timestamp.replace(tzinfo=timezone.utc)
            
            # now에 타임존 정보 추가
            if not now.tzinfo:
                now = now.replace(tzinfo=timezone.utc)
                
            time_diff_seconds = int((now - login_timestamp).total_seconds())
            duration_log_content = f"{position}*{name}*{time_diff_seconds}*{now.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # duration 로그 파일 생성 및 업로드
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                temp_file.write(duration_log_content)
                duration_temp_path = temp_file.name
            
            duration_filename = f"log_duration/{position}*{name}*{time_diff_seconds}*{timestamp}"
            duration_blob = bucket.blob(duration_filename)
            duration_blob.upload_from_filename(duration_temp_path)
            os.unlink(duration_temp_path)
        
        # 로그아웃 로그 파일 삭제 (업로드 후)
        os.unlink(temp_file_path)
        
        # 모든 로그아웃 로그 파일 삭제
        logout_blobs = list(bucket.list_blobs(prefix="log_logout/"))
        for blob in logout_blobs:
            try:
                # 현재 사용자의 로그아웃 파일만 삭제
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    blob.download_to_filename(temp_file.name)
                    with open(temp_file.name, 'r') as f:
                        content = f.read()
                    os.unlink(temp_file.name)
                
                parts = content.split('*')
                if len(parts) >= 4 and parts[0] == position and parts[1] == name:
                    blob.delete()
            except Exception as e:
                st.error(f"로그아웃 로그 파일 삭제 중 오류 발생: {str(e)}")
        
    except Exception as e:
        st.error(f"로그 파일 처리 중 오류 발생: {str(e)}")
    
    st.session_state.clear()
    st.success("로그아웃 되었습니다.")
