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

# 나머지 코드는 이전과 동일...
[이전 코드와 동일한 부분 생략]