"""
app.py
------
Streamlit front-end for the AI Customer Service Chatbot.

Responsibilities:
- Renders the chat UI and session-scoped history.
- Enforces input validation and rate limiting.
- Delegates all NLP/response logic to `src.chatbot.Chatbot`.
- Optionally generates voice replies via pyttsx3 (auto-disables itself
  gracefully on environments without a system TTS driver).
"""

import logging
import os
import tempfile
import threading
import time

import streamlit as st

from config import (
    HISTORY_LIMIT,
    INTENTS_PATH,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL,
    MAX_MESSAGE_LENGTH,
    RATE_LIMIT_SECONDS,
    TTS_RATE,
)
from src.chatbot import Chatbot

# ---------------- Setup Logging ---------------- #
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger(__name__)


# =========================================================
#  TTS ENGINE — Singleton, reused across all requests.
#  Initializing pyttsx3 per-message is expensive; a single reused
#  engine (behind a lock) keeps voice replies fast under load.
# =========================================================
_tts_lock = threading.Lock()
_tts_engine = None
TTS_AVAILABLE = True


def _init_tts_engine() -> None:
    """Initialize the TTS engine once. Disables the feature gracefully
    if unsupported (e.g. missing espeak driver on some servers)."""
    global _tts_engine, TTS_AVAILABLE
    try:
        import pyttsx3

        _tts_engine = pyttsx3.init()
        _tts_engine.setProperty("rate", TTS_RATE)
        TTS_AVAILABLE = True
        logger.info("TTS engine initialized successfully.")
    except Exception as e:
        TTS_AVAILABLE = False
        _tts_engine = None
        logger.warning("TTS unavailable on this system, disabling audio feature: %s", e)


_init_tts_engine()


def generate_audio_bytes(text: str):
    """Generate speech audio for `text`. Returns None if TTS is unavailable
    or generation fails (caller must handle None gracefully)."""
    if not TTS_AVAILABLE or not text:
        return None

    temp_path = None
    with _tts_lock:
        try:
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            _tts_engine.save_to_file(text, temp_path)
            _tts_engine.runAndWait()

            with open(temp_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error("TTS generation error: %s", e)
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as cleanup_error:
                    logger.warning("Could not remove temp file %s: %s", temp_path, cleanup_error)


# ---------------- Page Config ---------------- #
st.set_page_config(
    page_title="AI Customer Support Chatbot",
    page_icon="🤖",
    layout="centered",
)


# ---------------- Bot Loader ---------------- #
def load_bot() -> Chatbot:
    """Creates a fresh Chatbot instance, raising a clear error if
    intents.json is missing instead of an opaque exception."""
    if not INTENTS_PATH.exists():
        raise FileNotFoundError(f"intents.json not found at {INTENTS_PATH}")
    return Chatbot(str(INTENTS_PATH))


# ---------------- Session State (Multi-User Isolation) ---------------- #
if "messages" not in st.session_state:
    st.session_state.messages = []

if "bot" not in st.session_state:
    try:
        st.session_state.bot = load_bot()
    except Exception as e:
        logger.error("Failed to load Chatbot: %s", e)
        st.error("⚠️ System error: Chatbot failed to initialize. Please refresh the page.")
        st.stop()

if "last_msg_time" not in st.session_state:
    st.session_state.last_msg_time = 0.0

if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = TTS_AVAILABLE


# ---------------- Sidebar ---------------- #
with st.sidebar:
    st.title("🤖 Customer Support")
    st.markdown("---")

    st.write("### Features")
    st.write("✅ Smart NLP Matching (TF-IDF + Cosine Similarity)")
    st.write("✅ Chat History")
    st.write("✅ FAQ Bot")
    st.write("✅ Customer Support")

    st.markdown("---")

    if TTS_AVAILABLE:
        st.session_state.audio_enabled = st.toggle(
            "🔊 Voice replies", value=st.session_state.audio_enabled
        )
    else:
        st.caption("🔇 Voice replies unavailable on this server.")

    st.markdown("---")

    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        try:
            st.session_state.bot = load_bot()
        except Exception as e:
            logger.error("Failed to reload Chatbot on clear: %s", e)
            st.error("⚠️ Could not reset chatbot memory. Previous session kept.")
        st.rerun()


# ---------------- Main UI ---------------- #
st.title("🤖 AI Customer Service Chatbot")
st.caption("Ask me anything about orders, refunds, shipping, payments and support.")

# ---------------- Render Previous Chats ---------------- #
for chat in st.session_state.messages:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        st.write(chat["bot"])
        if chat.get("audio"):
            st.audio(chat["audio"], format="audio/wav")

# ---------------- User Input & Processing ---------------- #
user_message = st.chat_input("Type your message...")

if user_message:
    cleaned_message = user_message.strip()

    # 1. Input Validation
    if not cleaned_message:
        st.warning("Please enter a valid message.")
        st.stop()

    # 2. Length Guard (prevents oversized TTS/model calls from freezing the app)
    if len(cleaned_message) > MAX_MESSAGE_LENGTH:
        st.warning(f"Message too long. Please keep it under {MAX_MESSAGE_LENGTH} characters.")
        st.stop()

    # 3. Rate Limiting to prevent spam / accidental DoS
    current_time = time.time()
    if current_time - st.session_state.last_msg_time < RATE_LIMIT_SECONDS:
        st.warning("You're sending messages too fast. Please wait a moment.")
        st.stop()

    st.session_state.last_msg_time = current_time

    # Display user message instantly
    with st.chat_message("user"):
        st.write(cleaned_message)

    # Generate bot response (+ optional audio)
    try:
        with st.spinner("Typing..."):
            response = st.session_state.bot.get_response(cleaned_message)

            if not response or not str(response).strip():
                response = "Sorry, I couldn't understand that. Could you rephrase it?"

            audio_data = None
            if st.session_state.audio_enabled:
                audio_data = generate_audio_bytes(response)

        with st.chat_message("assistant"):
            st.write(response)
            if audio_data:
                st.audio(audio_data, format="audio/wav", autoplay=True)
            elif st.session_state.audio_enabled and TTS_AVAILABLE:
                st.caption("⚠️ Voice reply unavailable for this message.")

        # Save to session memory
        st.session_state.messages.append({
            "user": cleaned_message,
            "bot": response,
            "audio": audio_data,
        })

        # RAM Leak Prevention: Truncate history
        if len(st.session_state.messages) > HISTORY_LIMIT:
            st.session_state.messages = st.session_state.messages[-HISTORY_LIMIT:]

        logger.info("Interaction success - User: %r | Bot: %r", cleaned_message, response)

    except Exception as e:
        logger.error("Error handling message %r: %s", cleaned_message, e)
        st.error("Sorry, I encountered an issue while processing your request. Please try again.")
