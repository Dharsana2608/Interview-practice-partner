import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import base64
from io import BytesIO
import hashlib
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Technical Assessment Platform", page_icon="🏢", layout="wide")
load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

# --- DARK MODE & CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #0E1117; color: #FAFAFA; }
        section[data-testid="stSidebar"] { background-color: #1c1e24; }
        
        /* Chat Styling */
        .stChatMessage { padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #333; }
        .stChatMessage[data-testid="stChatMessageUser"] { background-color: #2C2F33; border-left: 5px solid #00C853; }
        .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: #1E2A38; border-left: 5px solid #2962FF; }
        
        /* Report Card Styling */
        .report-card { background-color: #1E2A38; padding: 30px; border-radius: 15px; border: 1px solid #444; }
        h1, h2, h3 { color: #E0E0E0 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. AUDIO ENGINE ---
def play_ai_voice(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode()
        audio_html = f"""<audio autoplay><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>"""
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# --- 3. STATE MANAGEMENT ---
if "messages" not in st.session_state: st.session_state.messages = [] # For Interview
if "lobby_messages" not in st.session_state: st.session_state.lobby_messages = [] # For Pre-Chat
if "interview_active" not in st.session_state: st.session_state.interview_active = False
if "feedback_mode" not in st.session_state: st.session_state.feedback_mode = False
if "question_count" not in st.session_state: st.session_state.question_count = 0
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None
if "final_report" not in st.session_state: st.session_state.final_report = ""
if "mic_activated_time" not in st.session_state: st.session_state.mic_activated_time = None
if "last_recording_state" not in st.session_state: st.session_state.last_recording_state = False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Configuration")
    role = st.text_input("Role", "Senior Backend Engineer")
    level = st.selectbox("Level", ["Junior", "Senior", "Lead"])
    st.divider()
    
    # Only show "Finish" if the interview is actually running
    if st.session_state.interview_active and not st.session_state.feedback_mode:
        st.write(f"📊 **Q{st.session_state.question_count} / 15**")
        if st.button("🏁 Submit & End Test"):
            st.session_state.interview_active = False
            st.session_state.feedback_mode = True
            st.rerun()

# --- 5. MAIN LOGIC FLOW ---

# ============================================================
# PHASE 1: THE LOBBY (Pre-Interview Chat)
# ============================================================
if not st.session_state.interview_active and not st.session_state.feedback_mode:
    st.title(f"🏢 Welcome to the {role} Assessment")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Instructions:**
        1. This is a voice-based technical assessment.
        2. You have **30 seconds** to start answering each question.
        3. If you don't know an answer, click 'Skip'.
        
        *If you have doubts about the process, ask the coordinator below.*
        """)
        
        # --- LOBBY CHAT UI ---
        chat_container = st.container(height=300)
        with chat_container:
            if not st.session_state.lobby_messages:
                st.info("👋 Hi! I am the Coordinator. Any questions before we start?")
            for msg in st.session_state.lobby_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # User asks a doubt
        if user_query := st.chat_input("Ask a doubt (e.g., 'What topics are covered?')"):
            st.session_state.lobby_messages.append({"role": "user", "content": user_query})
            
            # AI Coordinator Logic
            coordinator_prompt = f"""
            You are a helpful Interview Coordinator. The user is about to take a technical test for a {role} role.
            Answer their questions briefly and politely. Encourage them to start the test.
            """
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": coordinator_prompt}] + st.session_state.lobby_messages
            )
            st.session_state.lobby_messages.append({"role": "assistant", "content": response.choices[0].message.content})
            st.rerun()

    with col2:
        st.write("### Ready?")
        st.write("Click below to enter the assessment room. Once started, the timer begins.")
        if st.button("🚀 Start Assessment Now", type="primary", use_container_width=True):
            st.session_state.interview_active = True
            st.session_state.question_count = 1
            st.session_state.messages = []
            
            # OPENING QUESTION (Direct & Professional)
            opener = f"This is the {level} {role} assessment. Question 1: Introduce yourself and describe your technical stack."
            st.session_state.messages.append({"role": "assistant", "content": opener})
            st.rerun()

# ============================================================
# PHASE 2: ACTIVE INTERVIEW (Strict Mode)
# ============================================================
elif st.session_state.interview_active:
    st.subheader(f"🎙️ Technical Interview ({st.session_state.question_count}/15)")
    st.progress(min(st.session_state.question_count / 15, 1.0))

    # 1. Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 2. Auto-Play AI Voice
    last_msg = st.session_state.messages[-1]
    if last_msg["role"] == "assistant":
        msg_hash = hash(last_msg["content"])
        if "last_spoken_hash" not in st.session_state or st.session_state.last_spoken_hash != msg_hash:
            play_ai_voice(last_msg["content"])
            st.session_state.last_spoken_hash = msg_hash
            st.session_state.question_start_time = time.time()
            st.session_state.mic_activated_time = None  # Reset mic activation time for new question
            st.session_state.last_recording_state = False

    st.divider()

    # 3. Input Zone
    col1, col2, col3 = st.columns([1, 2, 1])
    user_input = ""
    is_timeout = False
    
    with col2:
        # Visual Timer
        st.components.v1.html(
            f"""<div style="color: #ff4b4b; text-align: center; font-family: sans-serif; font-weight: bold;">
            Time to answer: <span id="timer">30</span>s</div>
            <script>
            var t=30; setInterval(function(){{ if(t>0) document.getElementById("timer").innerHTML=t--; else document.getElementById("timer").innerHTML="LATE"; }}, 1000);
            </script>""", height=40
        )
        
        st.write("**Click Mic to Speak:**")
        audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#00C853", icon_size="3x")
        
        if st.button("➡️ Skip Question", use_container_width=True):
            user_input = "SKIP"

    # 4. Process Logic
    # Check for timeout: 30 seconds total or 10 seconds after mic activation
    current_time = time.time()
    
    # Check overall timeout (30 seconds from question start)
    if (current_time - st.session_state.question_start_time) > 30:
        is_timeout = True
    
    # Track mic activation for 10-second timeout
    # Since we can't directly detect when recording starts, we'll use this approach:
    # When audio_bytes appears, it means recording just completed. We estimate when it started.
    # We'll track the estimated start time and check if 10 seconds pass without completion.
    
    if audio_bytes:
        current_hash = hashlib.md5(audio_bytes).hexdigest()
        if current_hash != st.session_state.last_audio_hash:
            st.session_state.last_audio_hash = current_hash
            
            # When audio_bytes appears, recording just completed
            # Estimate recording started 3 seconds ago (typical duration)
            # We'll use this to track when the next recording might start
            estimated_recording_start = current_time - 3
            
            # Update activation time to current time for tracking next recording
            # This helps us detect if user starts a new recording but takes too long
            st.session_state.mic_activated_time = current_time
            
            if (current_time - st.session_state.question_start_time) > 30:
                is_timeout = True
            elif not is_timeout:
                with st.spinner("Transcribing..."):
                    with open("temp.wav", "wb") as f:
                        f.write(audio_bytes)
                    try:
                        transcript = client.audio.transcriptions.create(
                            model="whisper-large-v3-turbo",
                            file=open("temp.wav", "rb")
                        )
                        user_input = transcript.text
                        # Don't reset mic_activated_time here - keep it for next recording check
                    except:
                        pass
    else:
        # No audio_bytes yet - check if user started recording but hasn't completed it
        # Since we can't detect when recording starts directly, we use this approach:
        # After getting audio_bytes, we track the time. If 10+ seconds pass without new audio,
        # assume user might have started a new recording that's taking too long
        if st.session_state.mic_activated_time is not None:
            time_since_last_audio = current_time - st.session_state.mic_activated_time
            # If 10+ seconds passed since last audio and no new audio_bytes,
            # user might have started recording but it's taking more than 10 seconds
            if time_since_last_audio > 10:
                is_timeout = True

    # 5. AI Response Generation (Strict NO-FILLER Mode)
    if user_input or is_timeout:
        if is_timeout:
            st.session_state.messages.append({"role": "user", "content": "(Timeout)"})
            system_instruction = "User failed to answer in time. Ask the next technical question immediately. Do not lecture."
        
        elif user_input == "SKIP":
            st.session_state.messages.append({"role": "user", "content": "(Skipped)"})
            # SPECIAL INSTRUCTION FOR SKIP
            system_instruction = "User skipped the question. Ask a completely DIFFERENT technical question immediately. Do NOT say 'Noted' or 'Okay'. Just ask the question."
            
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            # SPECIAL INSTRUCTION FOR ANSWERS
            system_instruction = f"""
            You are a strict technical interviewer.
            Candidate just answered.
            Task: Ask the NEXT relevant technical question based on their answer or move to a new topic.
            CONSTRAINT: Do NOT use filler words like "Great", "Okay", "Noted", "Let's move on".
            CONSTRAINT: Start your response directly with the question (e.g., "How does garbage collection work in Java?").
            """

        with st.spinner("Evaluating..."):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_instruction}] + st.session_state.messages
            )
            ai_reply = completion.choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        st.session_state.question_count += 1
        
        if st.session_state.question_count > 15:
            st.session_state.interview_active = False
            st.session_state.feedback_mode = True
        
        st.rerun()

# ============================================================
# PHASE 3: REPORT CARD
# ============================================================
elif st.session_state.feedback_mode:
    st.title("📋 Final Assessment Report")
    
    if not st.session_state.final_report:
        with st.spinner("Generating decision..."):
            grading_prompt = f"""
            Assessment Complete. Review the transcript.
            Generate a concise report:
            1. Decision: (Hire / No Hire)
            2. Technical Score: (0-100)
            3. Weak Areas:
            """
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages + [{"role": "user", "content": grading_prompt}]
            )
            st.session_state.final_report = completion.choices[0].message.content

    st.markdown(f"<div class='report-card'>{st.session_state.final_report}</div>", unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 Start New Candidate"):
        st.session_state.clear()
        st.rerun()