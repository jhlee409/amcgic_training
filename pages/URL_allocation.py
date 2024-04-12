import os
import tkinter as tk
from tkinter import filedialog
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st

# Set page to wide mode
st.set_page_config(page_title="URL_allocation", layout="wide")

# 로그인 상태 확인
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    # Check if Firebase app has already been initialized
    if not firebase_admin._apps:
        # Firebase 설정 정보 로드
        cred = credentials.Certificate(r'"C:\Users\admin\OneDrive - UOU\LLM\project_bulletin\code_bulletin_all_user_erase_registration\amcgi-bulletin-4f317f4638ed.json"')
        firebase_admin.initialize_app(cred)

    # Firebase Storage에서 MP4 파일의 URL을 검색합니다.
    bucket = storage.bucket('amcgi-bulletin.appspot.com')

    # Tkinter 루트 윈도우 생성
    root = tk.Tk()
    root.withdraw()  # 루트 윈도우를 숨김

    # 파일 선택 대화상자 표시
    selected_files = filedialog.askopenfilenames()

    # 선택한 파일들에 대한 URL 생성
    file_urls = []
    for file_path in selected_files:
        file_name = os.path.basename(file_path)
        blob_path = f'AI_EGD_Dx_train/etc/{file_name}'
        blob = bucket.blob(blob_path)
        access_token = blob.generate_signed_url(expiration=3600)
        file_urls.append((file_name, access_token))

    # Tkinter 윈도우 생성
    result_window = tk.Toplevel(root)
    result_window.title('선택한 파일과 URL')

    # 파일 이름과 URL 표시
    for idx, (file_name, url) in enumerate(file_urls, start=1):
        tk.Label(result_window, text=f'파일 이름: {file_name}').grid(row=idx, column=0, sticky='w')
        tk.Label(result_window, text=f'URL: {url}').grid(row=idx, column=1, sticky='w')
        tk.Label(result_window, text='---').grid(row=idx+1, column=0, columnspan=2, sticky='w')

    # 루트 윈도우 실행
    root.mainloop()

    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.")