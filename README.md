# 🤖 AI Customer Service Chatbot

[![CI](https://github.com/manvendrasingh0712/customer-service-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/manvendrasingh0712/customer-service-chatbot/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/built%20with-Streamlit-FF4B4B)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **rule-based / simple NLP-based chatbot** that answers common customer
service queries — orders, refunds, shipping, payments, complaints — through
a clean chat interface, with optional voice replies.

Built to clearly demonstrate core **NLP techniques and chatbot design**
concepts: text preprocessing, TF-IDF vectorization, cosine similarity
matching, and rule-based fallback handling.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [How It Works (NLP Pipeline)](#-how-it-works-nlp-pipeline)
- [Project Structure](#-project-structure)
- [Features](#-features)
- [Setup & Installation](#-setup--installation)
- [Running the App](#-running-the-app)
- [Running Tests](#-running-tests)
- [Configuration](#-configuration)
- [Extending the Project](#-extending-the-project)
- [Tech Stack](#-tech-stack)
- [License](#-license)

---

## 🧠 Overview

This project implements a customer-support chatbot using a lightweight,
fully-explainable NLP pipeline rather than a black-box LLM — making it
ideal for demonstrating an understanding of foundational NLP and chatbot
design principles.

| | |
|---|---|
| **Type** | Rule-based + Simple NLP (TF-IDF + Cosine Similarity) |
| **Interface** | Streamlit web chat UI |
| **Voice support** | Optional text-to-speech replies (pyttsx3) |
| **Domain** | E-commerce / customer support (orders, refunds, shipping, payments) |

---

## ⚙️ How It Works (NLP Pipeline)

```
User Input
   │
   ▼
Preprocessing (lowercase, remove punctuation, remove stopwords)
   │
   ▼
TF-IDF Vectorization  (converts text -> numeric vectors)
   │
   ▼
Cosine Similarity vs. all known patterns in intents.json
   │
   ├── score ≥ 0.20  → matched intent  → random response from that intent
   └── score < 0.20  → fallback intent → "I didn't understand, could you rephrase?"
```

1. **Knowledge base (`intents.json`)** — organizes customer service topics
   into *intents*, each with sample `patterns` (things a user might type)
   and possible `responses`.
2. **Text preprocessing** — lowercasing, punctuation stripping, and stopword
   removal, implemented with a small built-in stopword list (no external
   NLTK downloads required — works fully offline).
3. **TF-IDF vectorization** — `sklearn.feature_extraction.text.TfidfVectorizer`
   converts every known pattern into a numeric vector at startup.
4. **Cosine similarity matching** — the user's message is vectorized the
   same way and compared against every known pattern to find the closest
   intent.
5. **Rule-based fallback** — if the best similarity score is below a
   confidence threshold, the bot admits it doesn't know rather than
   guessing incorrectly — this keeps responses trustworthy.

---

## 📂 Project Structure

```
customer-service-chatbot/
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions: lint + test on every push
├── .streamlit/
│   └── config.toml           # Theme & server config for deployment
├── src/
│   ├── __init__.py
│   └── chatbot.py            # NLP engine (TF-IDF + Cosine Similarity)
├── tests/
│   ├── __init__.py
│   └── test_chatbot.py       # 20 unit tests covering NLP matching & edge cases
├── app.py                    # Streamlit UI (chat, history, voice, rate limiting)
├── config.py                 # Centralized configuration constants
├── intents.json              # Knowledge base: intents, patterns, responses
├── requirements.txt          # Runtime dependencies
├── requirements-dev.txt      # Dev dependencies (pytest, flake8, black)
├── setup.cfg                 # Flake8 lint configuration
├── .gitignore
├── LICENSE
└── README.md
```

---

## ✅ Features

- Handles common customer service topics: order status, cancellations,
  refunds, returns, shipping, payments, complaints, discounts, and
  escalation to a human agent
- Confidence-based fallback — never confidently guesses the wrong answer
- Optional voice replies (toggle in sidebar); auto-disables gracefully on
  servers without a system TTS driver instead of crashing
- Session-isolated chat history (safe for multiple concurrent users)
- Memory-bounded history (prevents unbounded RAM growth in long sessions)
- Rate limiting to prevent spam / accidental abuse
- Input length validation
- Centralized configuration (`config.py`) for easy tuning
- Structured logging to both console and `chatbot.log`
- 20 automated unit tests + CI pipeline (GitHub Actions) running on
  Python 3.10, 3.11, and 3.12 on every push
- Linted with `flake8` (zero warnings)

---

## 🚀 Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/manvendrasingh0712/customer-service-chatbot.git
cd customer-service-chatbot

# 2. Create a virtual environment
python -m venv venv

# Activate it:
venv\Scripts\Activate.ps1     # Windows PowerShell
venv\Scripts\activate.bat     # Windows CMD
source venv/bin/activate      # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** Voice replies require a system TTS driver (e.g. `espeak` on
> Linux: `sudo apt-get install espeak`). If unavailable, the app detects
> this automatically and disables the voice feature instead of crashing.

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually `http://localhost:8501`).

---

## 🧪 Running Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Lint check:

```bash
flake8 .
```

---

## 🔧 Configuration

All tunable values live in `config.py`:

| Constant | Default | Purpose |
|---|---|---|
| `HISTORY_LIMIT` | 20 | Max messages kept per session |
| `RATE_LIMIT_SECONDS` | 1.5 | Minimum gap between messages |
| `MAX_MESSAGE_LENGTH` | 500 | Max characters per message |
| `CONFIDENCE_THRESHOLD` | 0.20 | Minimum similarity score to accept a match |
| `TTS_RATE` | 200 | Speech rate (words per minute) |

---

## 🧩 Extending the Project

- **Add more intents**: add new objects to `intents.json` with a `tag`,
  a list of `patterns`, and a list of `responses` — no code changes needed.
- **Improve NLP**: swap `TfidfVectorizer` for word embeddings (e.g. spaCy
  vectors or Sentence-Transformers) for more nuanced semantic matching.
- **Add conversational memory**: track the last matched intent in
  `st.session_state` to support multi-turn context (e.g. "cancel it"
  referring to a previously mentioned order).
- **Connect a real backend**: replace static responses with live calls to
  an orders/refunds API for real-time answers.
- **Containerize**: add a `Dockerfile` for one-command deployment.

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — web chat interface
- **scikit-learn** — TF-IDF vectorization & cosine similarity
- **pyttsx3** — offline text-to-speech
- **pytest** + **flake8** — testing & linting
- **GitHub Actions** — CI

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).