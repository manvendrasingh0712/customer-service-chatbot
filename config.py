"""
config.py
---------
Centralized configuration for the chatbot application.

Keeping all tunable constants in one place (instead of scattered across
app.py and src/chatbot.py) is a production best-practice: it makes the
app easier to tune, test, and deploy across different environments
without touching business logic.
"""

from pathlib import Path

# ---------------------------------------------------------------- #
# Paths
# ---------------------------------------------------------------- #
BASE_DIR: Path = Path(__file__).resolve().parent
INTENTS_PATH: Path = BASE_DIR / "intents.json"

# ---------------------------------------------------------------- #
# Chat behaviour
# ---------------------------------------------------------------- #
HISTORY_LIMIT: int = 20  # Max messages kept in memory per session
RATE_LIMIT_SECONDS: float = 1.5  # Minimum gap between two user messages
MAX_MESSAGE_LENGTH: int = 500  # Prevents oversized inputs from causing lag

# ---------------------------------------------------------------- #
# NLP engine (TF-IDF + Cosine Similarity)
# ---------------------------------------------------------------- #
CONFIDENCE_THRESHOLD: float = 0.20  # Below this similarity score -> fallback

# ---------------------------------------------------------------- #
# Text-to-Speech
# ---------------------------------------------------------------- #
TTS_RATE: int = 200  # Words per minute

# ---------------------------------------------------------------- #
# Logging
# ---------------------------------------------------------------- #
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_FILE: Path = BASE_DIR / "chatbot.log"
