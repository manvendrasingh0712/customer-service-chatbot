# 🏛️ System Architecture — AI Customer Service Chatbot

> Companion document to `README.md`. Contains full architecture diagrams: Mermaid (render + SVG-export ready), ASCII, Component, Sequence, Deployment, and Data Flow views.

---

## 1. Mermaid — High-Level Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        U["👤 User (Browser)"]
    end

    subgraph Presentation["Presentation Layer — app.py"]
        UI["Streamlit Chat UI<br/>message window · sidebar · controls"]
    end

    subgraph Application["Application Layer — app.py"]
        CC["Chat Controller"]
        RL["Rate Limiter<br/>(RATE_LIMIT_SECONDS)"]
        IV["Input Validator<br/>(MAX_MESSAGE_LENGTH)"]
        HM["History Manager<br/>(HISTORY_LIMIT, session_state)"]
    end

    subgraph Core["NLP Core — src/chatbot.py"]
        direction TB
        PP["Preprocessing<br/>lowercase · strip punctuation · stopwords"]
        TF["TF-IDF Vectorizer<br/>(sklearn)"]
        CS["Cosine Similarity Matcher"]
        TH{"score ≥ CONFIDENCE_THRESHOLD (0.20)?"}
        PP --> TF --> CS --> TH
    end

    subgraph Knowledge["Knowledge Base"]
        KB[("intents.json<br/>tags · patterns · responses")]
    end

    subgraph Output["Output Layer"]
        RG["Response Generator"]
        VE["Voice Engine — pyttsx3<br/>(optional, auto-disables if no TTS driver)"]
    end

    subgraph Cross["Cross-Cutting"]
        CFG["config.py<br/>centralized constants"]
        LOG["Structured Logging<br/>console + chatbot.log"]
    end

    U --> UI --> CC
    CC --> RL
    CC --> IV
    CC --> HM
    CC --> Core
    Core -.reads.-> KB
    TH -->|Yes| RG
    TH -->|No| RG
    RG --> U
    RG -.optional.-> VE -.-> U
    CFG -.configures.-> RL & IV & HM & TH & VE
    CC -.emits.-> LOG
    Core -.emits.-> LOG
```

---

## 2. SVG-Ready Mermaid Diagram

Use this block directly with `mmdc` (mermaid-cli) to export a standalone SVG:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i architecture.mmd -o architecture.svg -b transparent -w 1600 -H 1000
```

`architecture.mmd`:

```mermaid
%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#1f2937','primaryTextColor':'#f9fafb','primaryBorderColor':'#4b5563','lineColor':'#9ca3af','fontSize':'14px'}}}%%
flowchart LR
    U["👤 User"] --> UI["Streamlit UI"]
    UI --> CC["Chat Controller"]
    CC --> RL["Rate Limiter"]
    CC --> IV["Input Validator"]
    CC --> ENG["NLP Engine\n(src/chatbot.py)"]
    ENG --> PP["Preprocess"]
    PP --> TFIDF["TF-IDF Vectorize"]
    TFIDF --> COS["Cosine Similarity"]
    COS --> GATE{"score ≥ 0.20?"}
    GATE -->|Yes| MATCH["Matched Intent"]
    GATE -->|No| FALL["Fallback Response"]
    MATCH --> RESP["Response Generator"]
    FALL --> RESP
    RESP --> UI
    RESP -.-> TTS["pyttsx3 Voice (optional)"]
    KB[("intents.json")] -.-> ENG
    CFG["config.py"] -.-> RL & IV & GATE & TTS
    LOGF[("chatbot.log")] -.-> CC
```

---

## 3. High-Quality ASCII Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                               │
│                              👤  User (Browser)                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / WebSocket (Streamlit)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER  (app.py)                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │  Streamlit Chat UI                                              │   │
│   │  • message history panel   • sidebar (voice toggle / reset)     │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
└───────────────────────────────────┼────────────────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER  (app.py)                          │
│  ┌───────────────┐   ┌──────────────────┐   ┌─────────────────────┐    │
│  │ Chat Controller│──▶│  Rate Limiter    │   │  Input Validator     │   │
│  │  (orchestrates)│   │ (RATE_LIMIT_SEC) │   │ (MAX_MESSAGE_LENGTH) │   │
│  └───────┬───────┘   └──────────────────┘   └─────────────────────┘    │
│          │            ┌──────────────────┐                              │
│          └───────────▶│  History Manager │  (HISTORY_LIMIT,             │
│                        │                  │   st.session_state)         │
│                        └──────────────────┘                              │
└───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   NLP CORE LAYER  (src/chatbot.py)                      │
│                                                                          │
│   Preprocessing  ──▶  TF-IDF Vectorizer  ──▶  Cosine Similarity Match   │
│  (lowercase,          (sklearn                (score vs. every known    │
│   strip punct,         TfidfVectorizer)        pattern in intents.json) │
│   stopwords)                                                            │
│                                                        │                │
│                                             ┌──────────┴──────────┐     │
│                                             ▼                     ▼     │
│                                    score ≥ 0.20            score < 0.20 │
│                                    Matched Intent          Fallback     │
└───────────────────────────────────┬────────────────────────────────────┘
                                     │  reads (read-only, loaded at startup)
                        ┌────────────┴────────────┐
                        │      intents.json         │
                        │  {tag, patterns[], responses[]} │
                        └────────────┬────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        OUTPUT LAYER                                     │
│   ┌───────────────────────┐        ┌────────────────────────────┐      │
│   │  Response Generator    │───────▶│  Voice Engine (pyttsx3)     │      │
│   │ (random pick from      │        │  optional · TTS_RATE        │      │
│   │  matched responses[])  │        │  auto-disables w/o driver   │      │
│   └───────────┬────────────┘        └──────────────┬──────────────┘      │
└───────────────┼─────────────────────────────────────┼──────────────────┘
                 ▼                                     ▼
            back to UI                          spoken audio (optional)

┌────────────────────────────────────────────────────────────────────────┐
│  CROSS-CUTTING CONCERNS                                                 │
│  config.py  → HISTORY_LIMIT, RATE_LIMIT_SECONDS, MAX_MESSAGE_LENGTH,    │
│                CONFIDENCE_THRESHOLD, TTS_RATE                          │
│  logging    → console + chatbot.log (structured, all layers)           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Diagram

```mermaid
graph TB
    subgraph "app.py"
        C1["ChatController"]
        C2["RateLimiter"]
        C3["InputValidator"]
        C4["HistoryManager"]
        C5["SidebarControls"]
    end

    subgraph "src/chatbot.py"
        C6["Preprocessor"]
        C7["TfidfVectorizer (sklearn)"]
        C8["SimilarityMatcher"]
        C9["ResponseSelector"]
    end

    subgraph "config.py"
        C10["Config Constants"]
    end

    subgraph "Data"
        C11["intents.json"]
        C12["chatbot.log"]
    end

    subgraph "tests/test_chatbot.py"
        C13["20 Unit Tests"]
    end

    C1 --> C2
    C1 --> C3
    C1 --> C4
    C1 --> C5
    C1 --> C6
    C6 --> C7 --> C8 --> C9
    C8 -.reads.-> C11
    C9 -.reads.-> C11
    C10 -.configures.-> C2
    C10 -.configures.-> C3
    C10 -.configures.-> C4
    C10 -.configures.-> C8
    C1 -.writes.-> C12
    C13 -.tests.-> C6
    C13 -.tests.-> C7
    C13 -.tests.-> C8
    C13 -.tests.-> C9
```

**Component responsibilities**

| Component | File | Responsibility |
|---|---|---|
| `ChatController` | `app.py` | Orchestrates request lifecycle: validate → rate-limit → match → respond → log |
| `RateLimiter` | `app.py` | Enforces `RATE_LIMIT_SECONDS` gap between messages |
| `InputValidator` | `app.py` | Rejects messages exceeding `MAX_MESSAGE_LENGTH` |
| `HistoryManager` | `app.py` | Bounds session history to `HISTORY_LIMIT`, session-isolated |
| `Preprocessor` | `src/chatbot.py` | Lowercasing, punctuation stripping, stopword removal (built-in list, offline) |
| `TfidfVectorizer` | `src/chatbot.py` | Fits vocabulary from `intents.json` patterns at startup |
| `SimilarityMatcher` | `src/chatbot.py` | Computes cosine similarity, applies `CONFIDENCE_THRESHOLD` gate |
| `ResponseSelector` | `src/chatbot.py` | Picks a random response from the matched (or fallback) intent |
| `Config` | `config.py` | Single source of truth for all tunables |

---

## 5. Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant CC as ChatController
    participant RL as RateLimiter
    participant IV as InputValidator
    participant ENG as NLP Engine
    participant KB as intents.json
    participant RG as ResponseGenerator
    participant VE as VoiceEngine
    participant LOG as chatbot.log

    User->>UI: types message
    UI->>CC: submit(message)
    CC->>IV: validate(message)
    alt message too long
        IV-->>CC: reject
        CC-->>UI: show error
    else valid
        CC->>RL: check_rate_limit(session)
        alt too soon
            RL-->>CC: blocked
            CC-->>UI: "please wait" notice
        else allowed
            CC->>ENG: preprocess_and_match(message)
            ENG->>KB: load patterns (cached at startup)
            ENG->>ENG: TF-IDF vectorize
            ENG->>ENG: cosine similarity vs. all patterns
            alt score >= 0.20
                ENG-->>CC: matched_intent, score
            else score < 0.20
                ENG-->>CC: fallback_intent
            end
            CC->>RG: generate_response(intent)
            RG->>KB: pick random response
            RG-->>CC: response_text
            CC->>LOG: log(query, intent, score)
            CC-->>UI: append response to history
            opt voice enabled
                CC->>VE: speak(response_text)
                VE-->>User: audio output
            end
            UI-->>User: render response
        end
    end
```

---

## 6. Deployment Diagram

```mermaid
flowchart TB
    subgraph DevMachine["Developer Machine"]
        REPO["Git Repo (local clone)"]
        VENV["Python venv<br/>requirements.txt / requirements-dev.txt"]
    end

    subgraph GitHub["GitHub"]
        GH["Repository<br/>manvendrasingh0712/customer-service-chatbot"]
        GA["GitHub Actions CI<br/>ci.yml<br/>matrix: Python 3.10 / 3.11 / 3.12"]
        GA1["pytest -v (20 tests)"]
        GA2["flake8 lint"]
        GA --> GA1
        GA --> GA2
    end

    subgraph Cloud["Streamlit Community Cloud"]
        SCC["Streamlit Runtime Container"]
        APP["app.py entrypoint"]
        DEPS["requirements.txt deps<br/>(streamlit, scikit-learn, pyttsx3)"]
        STATIC["Static assets<br/>intents.json, config.py, src/"]
        SCC --> APP
        SCC --> DEPS
        SCC --> STATIC
    end

    subgraph EndUser["End User"]
        BROWSER["🌐 Web Browser"]
    end

    REPO -->|git push| GH
    GH -->|triggers on push/PR| GA
    GH -->|auto-deploy on main| SCC
    BROWSER -->|HTTPS| SCC
    SCC -->|renders UI, runs NLP| BROWSER

    note1["No external DB.<br/>No API keys.<br/>Fully self-contained,<br/>stateless per session."]
    SCC -.-> note1
```

**Deployment notes**

- No database, message broker, or external API — the entire app is a single Streamlit process reading `intents.json` from disk at startup.
- `pyttsx3` voice output depends on host TTS drivers (e.g. `espeak` on Linux); Streamlit Community Cloud containers may lack this — the app detects and disables voice gracefully rather than crashing.
- CI (GitHub Actions) is a build-time gate only; it does not participate in the runtime deployment path.
- Horizontal scaling = spinning up more identical stateless container instances (session state lives in Streamlit's per-session memory, not shared storage).

---

## 7. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        A["Raw user message<br/>(string)"]
    end

    subgraph L1["Level 1 — Validation & Control"]
        B["Length check<br/>(MAX_MESSAGE_LENGTH)"]
        C["Rate-limit check<br/>(RATE_LIMIT_SECONDS)"]
    end

    subgraph L2["Level 2 — Text Normalization"]
        D["Lowercase"]
        E["Strip punctuation"]
        F["Remove stopwords"]
    end

    subgraph L3["Level 3 — Vectorization"]
        G["TF-IDF transform<br/>(fitted vocabulary from intents.json)"]
    end

    subgraph L4["Level 4 — Matching"]
        H["Cosine similarity<br/>vs. all pattern vectors"]
        I{"max score ≥ 0.20?"}
    end

    subgraph L5["Level 5 — Response"]
        J["Select matched intent's responses[]"]
        K["Select fallback intent's responses[]"]
        L["Random choice → response string"]
    end

    subgraph L6["Level 6 — Delivery"]
        M["Append to session history<br/>(HISTORY_LIMIT bound)"]
        N["Render in Streamlit UI"]
        O["Optional: pyttsx3 speech synthesis"]
    end

    subgraph Persist["Persistent / Static Stores"]
        P[("intents.json<br/>read-only")]
        Q[("chatbot.log<br/>append-only")]
    end

    A --> B --> C --> D --> E --> F --> G
    P -.provides vocabulary at startup.-> G
    G --> H --> I
    P -.provides pattern vectors.-> H
    I -->|Yes| J
    I -->|No| K
    P -.provides responses.-> J
    P -.provides responses.-> K
    J --> L
    K --> L
    L --> M --> N
    L -.-> O
    B -.on failure.-> Q
    C -.on failure.-> Q
    L -->|log query+intent+score| Q
```

**Data flow summary**

| Stage | Input | Transformation | Output |
|---|---|---|---|
| Validation | Raw string | Length + rate-limit checks | Accepted / rejected message |
| Normalization | Accepted message | Lowercase, punctuation strip, stopword removal | Clean token string |
| Vectorization | Clean tokens | TF-IDF transform (fixed vocab from `intents.json`) | Numeric vector |
| Matching | Vector | Cosine similarity vs. pattern vectors | Best-match score + intent tag |
| Response | Intent tag | Threshold gate (0.20) → response pool lookup | Response string |
| Delivery | Response string | Append to bounded history, render, optional TTS | UI update + optional audio |
| Observability | Every stage | Structured log write | `chatbot.log` entry |

---

*Generated to accompany the `customer-service-chatbot` README — reflects the actual `app.py` / `src/chatbot.py` / `config.py` / `intents.json` structure with no invented components.*
