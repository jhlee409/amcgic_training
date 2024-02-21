import streamlit as st
import time
from PIL import Image
import docx
import io
from openai import OpenAI
import firebase_admin
from firebase_admin import credentials, storage

# Set page to wide mode
st.set_page_config(page_title="AI_EGD_Dx", layout="wide")

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
    st.subheader("AI_EGD_Dx_training")
    with st.expander(" 반드시 순서대로 해야 정상 작동합니다. 먼저 여기를 눌러 사용방법을 확인하세요."):
        st.write("- 가장 먼저 F1용인지 F2용인지를 선택합니다.")
        st.write("- EGD png 파일을 선택해서 업로드 하세요.")
        st.write("- 다음으로 '이전 대화기록 삭제버튼'을 눌러 이전 기록을 삭제해야 정상 작동합니다. 제대로 작동하지 않으면 한 번 더 누르세요")
        st.write("- 삭제가 완료되면, case instruction 파일을 upload 하세요.")
        st.write("- 각 단계마다 반드시 '열일 중' 스핀이 멈출 때까지 기다리세요. 스핀 돌 때 다른 버튼 누르면 오류납니다.")
        st.write("- impression을 입력하고 잠시 기다리면 정답과 비교를 해서 점수를 산출해 주고, 선생님에게 질문을 2개 정도 합니다. 그에 대해 답을 하면 권장 답안과 비교해 줍니다.")
        st.write("- 여러가지 기술적인 이유로 장기, 부위, 위치, 특히 크기를 채점하지 않습니다. 중요하지 않아서 그런다고 오해하지 않기를 당부합니다.")
        st.write("- '이것이 필요한가요?' 물으면 '그것은 필요합니다.'라고 질문에 상응하는 대답을 해야지 '그걸 하는 것이 적당하다고 판단합니다.' 이렇게 돌려 말하면 잘 못알아 먹습니다.^^;")
        st.write("- 두 개의 질문이 끝나도 궁금한 점이 있으면 물어보세요. 적절한 질문을 하면 적절한 대답을 해 줍니다.")
        st.write("- 같은 컴퓨터를 적절한 방법으로 계속 사용하면 이 AI는 그 방식에 익숙해지는 지 오류가 적어집니다. 반대로 해오던 방식을 갑자기 바꾸면 오류가 많이 납니다. 여러분도 경험해 보세요.")
        
    # Firebase에서 이미지를 다운로드하고 PIL 이미지 객체로 열기
    def download_and_open_image(bucket_name, file_path):
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_path)
        # BytesIO 객체를 사용하여 메모리에서 이미지를 직접 열기
        image_stream = io.BytesIO()
        blob.download_to_file(image_stream)
        image_stream.seek(0)
        return Image.open(image_stream)

    # # Function to display image in sidebar or main page
    # def display_large_image(image):
    #     with st.expander("Full-size Image"):
    #         st.image(image, use_column_width=True)
        
        # Function to list files in a specific directory in Firebase Storage
    def png_list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        file_names = []
        for blob in blobs:
            # Extracting file name from the path and adding to the list
            file_name = blob.name[len(directory):]  # Remove directory path from file name
            if file_name:  # Check to avoid adding empty strings (in case of directories)
                file_names.append(file_name)
        return file_names
    
    # F1 or F2 selection
    folder_selection = st.sidebar.radio("Select Folder", ["F1", "F2"])

    if folder_selection == "F1":
        directory_images = "AI_EGD_Dx_training/F1/images/"
        directory_instructions = "AI_EGD_Dx_training/F1/instructions/"
    else:
        directory_images = "AI_EGD_Dx_training/F2/images/"
        directory_instructions = "AI_EGD_Dx_training/F2/instructions/"

    # List and select PNG files
    file_list_images = png_list_files('amcgi-bulletin.appspot.com', directory_images)
    selected_image_file = st.sidebar.selectbox(f"{folder_selection}용: EGD png 사진을 선택하세요.", file_list_images)

    # Display the selected image
    if selected_image_file:
        selected_image_path = directory_images + selected_image_file
        image = download_and_open_image('amcgi-bulletin.appspot.com', selected_image_path)
        st.image(image, width=500)
    
    # with st.expander("Full-size Image"):
    #             st.image(image, use_column_width=True)
            
    st.sidebar.divider()

    # Function to list files in a specific directory in Firebase Storage
    def list_files(bucket_name, directory):
        bucket = storage.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=directory)
        file_names = []
        for blob in blobs:
            # Extracting file name from the path and adding to the list
            file_name = blob.name[len(directory):]  # Remove directory path from file name
            if file_name:  # Check to avoid adding empty strings (in case of directories)
                file_names.append(file_name)
        return file_names

    # Function to read file content from Firebase Storage
    def read_docx_file(bucket_name, file_name):
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_name)
        
        # Download the file to a temporary location
        temp_file_path = "/tmp/tempfile.docx"
        blob.download_to_filename(temp_file_path)
        
        # Read the content of the DOCX file
        doc = docx.Document(temp_file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        
        # Join the text into a single string
        return '\n'.join(full_text)
    
    # List and select DOCX files
    file_list_instructions = list_files('amcgi-bulletin.appspot.com', directory_instructions)
    selected_instruction_file = st.sidebar.selectbox(f"{folder_selection}용: case instruction 파일을 선택하세요.", file_list_instructions)

    # Read and display the content of the selected DOCX file
    if selected_instruction_file:
        full_path = directory_instructions + selected_instruction_file
        prompt = read_docx_file('amcgi-bulletin.appspot.com', full_path)
        st.session_state['prompt'] = prompt
        #st.text(prompt)  # Display the content of the docx file as text
        
    st.sidebar.divider()

    # Manage thread id
    if 'thread_id' not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    thread_id = st.session_state.thread_id

    assistant_id = "asst_AyqS2LqfxPw2RwRV1sl1bGhd"

    # Get user input from chat nput
    user_input = st.chat_input("입력창입니다. 선생님의 message를 여기에 입력하고 엔터를 치세요")

    # 사용자 입력이 있을 경우, prompt를 user_input으로 설정
    if user_input:
        prompt = user_input

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=prompt
    )

    # # 입력한 메세지 UI에 표시
    # if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    #     with st.chat_message(message.role):
    #         st.write(message.content[0].text.value)

    #RUN을 돌리는 과정
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    with st.spinner('열일 중...'):
        #RUN이 completed 되었나 1초마다 체크
        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

    #while문을 빠져나왔다는 것은 완료됐다는 것이니 메세지 불러오기
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )

    # # assistant 메세지 UI에 추가하기
    # #if message.content and message.content[0].text.value and '전체 지시 사항' not in message.content[0].text.value:
    # with st.chat_message(messages.data[0].role):
    #     st.write(messages.data[0].content[0].text.value)

    #메세지 모두 불러오기
    thread_messages = client.beta.threads.messages.list(thread_id, order="asc")

    # Clear button in the sidebar
    st.sidebar.write('instruction 파일 올리기전 먼저 누르세요.')
    if st.sidebar.button('이전 대화기록 삭제 버튼'):
        # Reset the prompt, create a new thread, and clear the docx_file and messages
        prompt = []
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        docx_file = None
        st.session_state['messages'] = []
        # Instead of directly modifying msg.content[0].text.value, which can cause an IndexError,
        # You should check if 'content' and 'text' exist before trying to modify them.
        for msg in thread_messages.data:
            if msg.content and len(msg.content) > 0 and 'text' in msg.content[0]:
                msg.content[0].text.value = ""

    st.sidebar.divider()
    # 로그아웃 버튼 생성
    if st.sidebar.button('로그아웃'):
        st.session_state.logged_in = False
        st.experimental_rerun()  # 페이지를 새로고침하여 로그인 화면으로 돌아감

    for msg in thread_messages.data:
        # 메시지 내용 확인 및 필터링 조건 추가
        if msg.content and msg.content[0].text.value:
            content = msg.content[0].text.value
            # 필터링 조건: 내용이 비어있지 않고, '..', '...', '전체 지시 사항'을 포함하지 않는 경우에만 UI에 표시
            if content.strip() not in ['', '..', '...'] and '전체 지시 사항' not in content:
                with st.chat_message(msg.role):
                    st.write(content)
        
else:
    # 로그인이 되지 않은 경우, 로그인 페이지로 리디렉션 또는 메시지 표시
    st.error("로그인이 필요합니다.") 