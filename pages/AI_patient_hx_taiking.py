import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
import speech_recognition as sr
import threading
from gtts import gTTS
import os
import tempfile
from audio_recorder_streamlit import audio_recorder
import io
from pydub import AudioSegment
from pydub.playback import play

# Set page to wide mode
st.set_page_config(page_title="AI Hx. taking", page_icon=":robot_face:", layout="wide")

def text_to_speech(text):
    """Convert text to speech and play it"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts = gTTS(text=text, lang='ko')
        tts.save(fp.name)
        st.audio(fp.name)
    os.unlink(fp.name)

def process_audio(audio_bytes):
    """Convert audio bytes to text using speech recognition"""
    if audio_bytes is None:
        return None
    
    # Convert audio bytes to AudioSegment
    audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
    
    # Export as WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
        audio.export(fp.name, format='wav')
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Read the temporary file
        with sr.AudioFile(fp.name) as source:
            audio_data = r.record(source)
            
            try:
                # Recognize speech using Google Speech Recognition
                text = r.recognize_google(audio_data, language='ko-KR')
                return text
            except sr.UnknownValueError:
                st.error("음성을 인식할 수 없습니다.")
                return None
            except sr.RequestError:
                st.error("음성 인식 서비스에 접근할 수 없습니다.")
                return None
            finally:
                os.unlink(fp.name)

if st.session_state.get('logged_in'):
    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    # Initialize OpenAI client
    client = OpenAI()

    # Firebase initialization (same as original code)
    if not firebase_admin._apps:
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

    # Firebase functions (same as original)
    def list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        file_names = []
        for blob in blobs:
            file_name = blob.name[len(directory):]
            if file_name:
                file_names.append(file_name)
        return file_names

    def read_docx_file(bucket_name, file_name):
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        temp_file_path = "/tmp/tempfile.docx"
        blob.download_to_filename(temp_file_path)
        
        doc = docx.Document(temp_file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        
        return '\n'.join(full_text)

    def get_file_content(bucket_name, directory, file_name):
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(directory + file_name)
        return blob.download_as_bytes()

    # Layout setup
    main_container = st.container()
    message_container = st.container()
    col1, col2 = st.columns([3, 1])

    with col1:
        message_container = st.container()
        message_container.markdown(
            """
            <style>
            .message-container {
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                height: 600px;
                overflow-y: auto;
            }
            .message-container p {
                text-align: left;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        message_box = message_container.empty()
        if 'message_box' not in st.session_state:
            st.session_state.message_box = ""

    with col2:
        # File selection
        case_directory = "AI_patient_Hx_taking/case/"
        case_file_list = list_files('amcgi-bulletin.appspot.com', case_directory)
        selected_case_file = st.sidebar.selectbox("증례 파일을 선택하세요.", case_file_list)

        if selected_case_file:
            case_full_path = case_directory + selected_case_file
            prompt = read_docx_file('amcgi-bulletin.appspot.com', case_full_path)
            st.session_state['prompt'] = prompt

            reference_directory = "AI_patient_Hx_taking/reference/"
            reference_file_list = list_files('amcgi-bulletin.appspot.com', reference_directory)
            excel_file = selected_case_file.replace('.docx', '.xlsx')
            if excel_file in reference_file_list:
                file_content = get_file_content('amcgi-bulletin.appspot.com', reference_directory, excel_file)
                st.sidebar.download_button(
                    label="Case 해설 자료 다운로드",
                    data=file_content,
                    file_name=excel_file,
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                st.sidebar.warning("해당하는 엑셀 파일이 없습니다.")

    # Voice input/output section
    input_container = st.container()
    with input_container:
        col3, col4 = st.columns([1, 1])
        
        with col3:
            st.write("음성으로 질문하기")
            audio_bytes = audio_recorder()
            if audio_bytes:
                user_input = process_audio(audio_bytes)
                if user_input:
                    st.write(f"인식된 텍스트: {user_input}")
                    
                    # Process the user input through OpenAI
                    message = client.beta.threads.messages.create(
                        thread_id=st.session_state.thread_id,
                        role="user",
                        content=user_input
                    )

                    run = client.beta.threads.runs.create(
                        thread_id=st.session_state.thread_id,
                        assistant_id=assistant_id,
                    )

                    with st.spinner('응답 생성 중...'):
                        while run.status != "completed":
                            time.sleep(1)
                            run = client.beta.threads.runs.retrieve(
                                thread_id=st.session_state.thread_id,
                                run_id=run.id
                            )

                    messages = client.beta.threads.messages.list(
                        thread_id=st.session_state.thread_id
                    )

                    # Convert assistant's response to speech
                    if messages.data[0].role == "assistant":
                        response_text = messages.data[0].content[0].text.value
                        st.session_state.message_box += f"🤖: {response_text}\n\n"
                        message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)
                        text_to_speech(response_text)

        with col4:
            st.write("또는 텍스트로 입력하기")
            text_input = st.text_input("텍스트 입력:", key="text_input")
            if text_input:
                message = client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=text_input
                )

    # Clear conversation button and logout (same as original)
    st.sidebar.divider()
    if st.sidebar.button('이전 대화기록 삭제 버튼'):
        st.session_state.thread_id = client.beta.threads.create().id
        st.session_state['messages'] = []
        st.session_state.message_box = ""
        message_container.markdown("", unsafe_allow_html=True)

    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.rerun()

else:
    st.error("로그인이 필요합니다.")