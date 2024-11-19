import streamlit as st
import time
import docx
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage
import streamlit.components.v1 as components
import ssl
import os

# SSL 인증서 검증 우회 설정 (로컬 개발 환경용)
if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

# Set page to wide mode
st.set_page_config(page_title="AI Hx. taking", page_icon=":robot_face:", layout="wide")

# HTML/JavaScript for voice recognition with error handling
def voice_input_component():
    return components.html(
        """
        <div>
            <button id="startButton" onclick="startRecording()">음성 입력 시작</button>
            <button id="stopButton" onclick="stopRecording()" disabled>중지</button>
            <p id="status"></p>
            <p id="result"></p>
        </div>

        <script>
        let recognition = null;
        
        function checkBrowserSupport() {
            if (!window.webkitSpeechRecognition && !window.SpeechRecognition) {
                document.getElementById('status').textContent = '죄송합니다. 이 브라우저는 음성 인식을 지원하지 않습니다. Chrome 브라우저를 사용해주세요.';
                document.getElementById('startButton').disabled = true;
                return false;
            }
            return true;
        }
        
        function startRecording() {
            if (!checkBrowserSupport()) return;
            
            try {
                recognition = new (window.webkitSpeechRecognition || window.SpeechRecognition)();
                recognition.lang = 'ko-KR';
                recognition.continuous = true;
                recognition.interimResults = true;
                
                document.getElementById('startButton').disabled = true;
                document.getElementById('stopButton').disabled = false;
                document.getElementById('status').textContent = '듣는 중...';
                
                recognition.onstart = function() {
                    document.getElementById('status').textContent = '음성 인식이 시작되었습니다.';
                };
                
                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    document.getElementById('status').textContent = '오류 발생: ' + event.error;
                    stopRecording();
                };
                
                recognition.onend = function() {
                    document.getElementById('status').textContent = '음성 인식이 종료되었습니다.';
                    document.getElementById('startButton').disabled = false;
                    document.getElementById('stopButton').disabled = true;
                };
                
                recognition.onresult = function(event) {
                    let finalTranscript = '';
                    let interimTranscript = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        const transcript = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {
                            finalTranscript += transcript;
                        } else {
                            interimTranscript += transcript;
                        }
                    }
                    
                    if (finalTranscript) {
                        document.getElementById('result').textContent = finalTranscript;
                        // Send result to Streamlit
                        window.parent.postMessage({
                            type: 'voice_input', 
                            value: finalTranscript
                        }, '*');
                    }
                    
                    if (interimTranscript) {
                        document.getElementById('result').textContent = '인식 중: ' + interimTranscript;
                    }
                };
                
                recognition.start();
                
            } catch (error) {
                console.error('Speech recognition initialization error:', error);
                document.getElementById('status').textContent = '음성 인식 초기화 중 오류가 발생했습니다.';
                document.getElementById('startButton').disabled = false;
            }
        }
        
        function stopRecording() {
            if (recognition) {
                try {
                    recognition.stop();
                } catch (error) {
                    console.error('Error stopping recognition:', error);
                }
                recognition = null;
                document.getElementById('startButton').disabled = false;
                document.getElementById('stopButton').disabled = true;
                document.getElementById('status').textContent = '음성 입력이 중지되었습니다.';
            }
        }
        
        // Cleanup on page unload
        window.onbeforeunload = function() {
            stopRecording();
        };
        
        // Initial browser support check
        checkBrowserSupport();
        </script>
        """,
        height=150,
    )

# Text-to-speech component with Windows compatibility
def voice_output_component(text):
    return components.html(
        f"""
        <script>
        function speak(text) {{
            try {{
                if (!window.speechSynthesis) {{
                    console.error('Speech synthesis not supported');
                    return;
                }}
                
                // Cancel any ongoing speech
                window.speechSynthesis.cancel();
                
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.lang = 'ko-KR';
                
                // Get available voices
                let voices = window.speechSynthesis.getVoices();
                
                // If voices are not immediately available, wait for them
                if (voices.length === 0) {{
                    window.speechSynthesis.onvoiceschanged = function() {{
                        voices = window.speechSynthesis.getVoices();
                        // Try to find a Korean voice
                        const koreanVoice = voices.find(voice => 
                            voice.lang.includes('ko') || 
                            voice.name.includes('Korean')
                        );
                        if (koreanVoice) {{
                            utterance.voice = koreanVoice;
                        }}
                        window.speechSynthesis.speak(utterance);
                    }};
                }} else {{
                    // Try to find a Korean voice
                    const koreanVoice = voices.find(voice => 
                        voice.lang.includes('ko') || 
                        voice.name.includes('Korean')
                    );
                    if (koreanVoice) {{
                        utterance.voice = koreanVoice;
                    }}
                    window.speechSynthesis.speak(utterance);
                }}
                
                // Handle errors
                utterance.onerror = function(event) {{
                    console.error('Speech synthesis error:', event);
                }};
                
            }} catch (error) {{
                console.error('Speech synthesis error:', error);
            }}
        }}
        
        // Wait for page to load before speaking
        window.onload = function() {{
            setTimeout(() => speak("{text}"), 100);
        }};
        </script>
        """,
        height=0,
    )

if st.session_state.get('logged_in'):
    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
        
    if 'thread_id' not in st.session_state:
        client = OpenAI()
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Initialize OpenAI client
    client = OpenAI()

    # Firebase initialization
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

    # Display Form Title
    main_container.subheader("AMC GI:&emsp;AI 환자 병력 청취 훈련 챗봇&emsp;&emsp;&emsp;v 1.5.0")
    with main_container.expander("정상적이 작동을 위해, 반드시 먼저 여길 눌러서 사용방법을 읽어 주세요."):
        st.write("- 처음에는 왼쪽 sidebar에서 증례 파일을 선택해 주세요.")
        st.write("- case가 준비되면 '어디가 불편해서 오셨나요?'로 문진을 시작하세요.")
        st.write("- 문진을 마치는 질문은 '알겠습니다. 혹시 궁금한 점이 있으신가요?' 입니다.")
        st.write("- 마지막에는 선생님이 물어보지 않은 중요 항목을 보여주게 되는데, 이 과정이 좀 길게 걸릴 수 있으니, 기다려 주세요.^^")
        st.write("- 다른 증례를 선택하기 전에 반드시 '이전 대화기록 삭제버튼'을  한 번 누른 후 다른 증례를 선택하세요.")
        st.write("- 증례 해설 자료가 필요하시면 다운로드 하실 수 있는데, 전체가 refresh 되므로 도중에 다운로드 하지 마시고, 마지막에 다운로드해 주세요.")

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
            voice_input_component()

        with col4:
            st.write("또는 텍스트로 입력하기")
            text_input = st.text_input("텍스트 입력:", key="text_input")

    # Process input (both voice and text)
    def process_input(user_input):
        if user_input:
            # Add user message to chat
            st.session_state.message_box += f"사용자: {user_input}\n\n"
            
            # Process with OpenAI
            message = client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_input
            )

            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id="asst_ecq1rotgT4c3by2NJBjoYcKj"
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

            if messages.data[0].role == "assistant":
                response_text = messages.data[0].content[0].text.value
                st.session_state.message_box += f"🤖: {response_text}\n\n"
                message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)
                voice_output_component(response_text)

    # Handle voice input from JavaScript
    if st.session_state.get('voice_input'):
        user_input = st.session_state.voice_input
        st.session_state.voice_input = None  # Clear the input
        
        # Process voice input (same as text input processing)
        client = OpenAI()
        message = client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id="asst_ecq1rotgT4c3by2NJBjoYcKj"
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

        if messages.data[0].role == "assistant":
            response_text = messages.data[0].content[0].text.value
            st.session_state.message_box += f"🤖: {response_text}\n\n"
            message_container.markdown(st.session_state.message_box, unsafe_allow_html=True)
            voice_output_component(response_text)

    # Clear conversation button and logout
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