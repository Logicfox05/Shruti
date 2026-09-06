# 🏢 SmartHire Finance — AI Candidate Assessment & Hiring Intelligence

> **Full-Stack AI-Powered Recruitment Assessment Platform for Packaging & Manufacturing Finance Roles**
> (Corrugation, Cartons, Flexible Packaging, Labels)

A production-grade, single-command web application that automates the entire candidate screening lifecycle — from resume upload & intelligent parsing → timed proctored MCQ assessment → AI-driven hiring intelligence report for managers.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Question Engine & Composition](#-question-engine--composition)
- [Resume Parser & Domain Detection](#-resume-parser--domain-detection)
- [Proctoring Engine](#-proctoring-engine)
- [Manager Dashboard & Hiring Intelligence](#-manager-dashboard--hiring-intelligence)
- [API Endpoints](#-api-endpoints)
- [Database Schema](#-database-schema)
- [Docker Deployment](#-docker-deployment)

---

## ✨ Key Features

### 🎯 Candidate Portal
- **One-Click Resume Upload** — Supports PDF & DOCX. Instantly extracts name, email, phone, degree, CGPA, and technical skills.
- **Live Skill Badge Preview** — Displays extracted competencies as interactive badges before the candidate even submits registration.
- **80-Question Timed Assessment** — 60-minute countdown timer with auto-submit on expiry.
- **Question Navigation Palette** — Visual grid showing answered (green), flagged (orange), and unanswered (gray) questions.
- **Auto-Save** — Every answer is saved to the server in real time. No data loss on accidental browser closure.
- **Fullscreen Lock** — Exam launches in fullscreen mode with proctoring alerts on exit.

### 🧠 AI Question Engine
- **1,000-Question Backend Repository** — 750 Indian Accounting & Taxation MCQs + 250 IQ & Workplace Adaptability MCQs.
- **Dynamic Randomization** — Every candidate receives a unique randomized question set on each login. No two candidates get the same paper.
- **Multi-Domain Resume Verification** — 16 custom questions dynamically generated from the candidate's actual uploaded resume (AI/ML, Software Engineering, or Finance).
- **3-Tier Cognitive Difficulty** — Questions categorized as Basic, Intermediate, and Advanced for multi-level competency assessment.

### 🔒 Background Proctoring Engine
- Tab switch detection (visibility change API)
- Window blur / Alt+Tab detection
- Fullscreen exit monitoring
- Copy-paste attempt blocking
- Right-click context menu lock

### 📊 Manager Intelligence Dashboard
- **Candidate Leaderboard** — Sortable table of all candidates with scores, verdicts, and integrity ratings.
- **Detailed Candidate Modal** — Click any candidate to view full hiring intelligence report.
- **3-Tier Cognitive Breakdown** — Visual gauges for Basic, Intermediate, and Advanced tier performance.
- **Cross-Role Placement Engine** — AI recommends whether the candidate is suited for Accountant, Senior Accountant, or Finance Manager based on tier performance.
- **Resume vs. Reality Audit Table** — Side-by-side comparison of claimed resume skills vs. actual test performance.
- **Radar Chart** — 6-pillar competency visualization (AP/P2P, AR/O2C, GST/TDS, Inventory, Banking/MIS, IQ/Adaptability).
- **Proctoring Integrity Score** — Deductions for tab switches, fullscreen exits, and paste attempts.
- **Suggested Interview Questions** — Auto-generated follow-up questions based on the candidate's weakest areas.
- **Print Report** — Multi-page A4 executive PDF report with canvas-to-PNG chart snapshots.

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vanilla JS)                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Candidate Portal│  │  Manager Portal  │  │  Proctoring UI   │  │
│  │  (Registration,  │  │  (Leaderboard,   │  │  (Tab/Blur/Copy  │  │
│  │   Exam, Timer)   │  │   Reports, Print)│  │   Detection)     │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
└───────────┼──────────────────────┼──────────────────────┼───────────┘
            │         REST API (JSON)          │
┌───────────┼──────────────────────┼──────────────────────┼───────────┐
│           ▼                      ▼                      ▼           │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Backend                           │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │    │
│  │  │Candidate │ │Assessment│ │ Manager  │ │  Proctoring  │   │    │
│  │  │ Router   │ │ Router   │ │ Router   │ │   Router     │   │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │    │
│  │       │             │            │              │           │    │
│  │  ┌────▼─────────────▼────────────▼──────────────▼───────┐   │    │
│  │  │                  SERVICES LAYER                       │   │    │
│  │  │  ResumeParser │ QuestionBank │ AIEngine │ Scoring     │   │    │
│  │  └──────────────────────┬────────────────────────────────┘   │    │
│  │                         │                                    │    │
│  │  ┌──────────────────────▼────────────────────────────────┐   │    │
│  │  │              SQLite Database (smarthire.db)            │   │    │
│  │  │  Candidates │ Sessions │ Questions │ ProctoringEvents  │   │    │
│  │  └───────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                         BACKEND                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer        | Technology                                                        |
|:-------------|:------------------------------------------------------------------|
| **Backend**  | Python 3.13, FastAPI, Uvicorn, SQLAlchemy ORM, Pydantic v2        |
| **Frontend** | HTML5, Bootstrap 5.3, Vanilla JavaScript, Chart.js, Font Awesome  |
| **Database** | SQLite (zero-config, file-based)                                  |
| **Resume**   | pypdf (PDF extraction), python-docx (DOCX extraction)             |
| **Deploy**   | Docker, docker-compose                                            |

---

## 📁 Project Structure

```
smarthire-finance/
├── run.py                          # Single-command entry point (python run.py)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker containerization
├── docker-compose.yml              # Docker Compose orchestration
├── README.md                       # This file
│
├── backend/
│   ├── smarthire.db                # SQLite database (auto-created on first run)
│   ├── uploads/                    # Uploaded resume files (PDF/DOCX)
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app factory & static file mount
│       ├── config.py               # Configuration & environment variables
│       ├── database.py             # SQLAlchemy engine & session factory
│       ├── models.py               # ORM models (Candidate, Session, Question, Proctoring)
│       ├── schemas.py              # Pydantic request/response schemas
│       │
│       ├── routers/
│       │   ├── candidate.py        # /api/candidate/* (register, parse-resume-preview)
│       │   ├── assessment.py       # /api/assessment/* (start, autosave, submit)
│       │   ├── manager.py          # /api/manager/* (candidates list, report)
│       │   └── proctoring.py       # /api/proctoring/* (log events)
│       │
│       ├── services/
│       │   ├── resume_parser.py    # Multi-domain PDF/DOCX text extraction & skill detection
│       │   ├── question_bank.py    # Random sampler from 1,000-question repository
│       │   ├── ai_engine.py        # Resume verification questions & hiring report generator
│       │   ├── scoring.py          # Objective score calculator
│       │   └── adaptive_engine.py  # Adaptive difficulty engine
│       │
│       └── data/
│           ├── repository_finance_750.json   # 750 Indian Accounting & Taxation MCQs
│           ├── repository_iq_250.json        # 250 IQ & Workplace Adaptability MCQs
│           └── question_repository_1000.json # Combined 1,000-question master repository
│
└── frontend/
    ├── index.html                  # Main SPA (Candidate + Manager portals)
    ├── candidate.html              # Standalone candidate portal
    ├── manager.html                # Standalone manager portal
    ├── favicon.ico
    ├── css/
    │   └── styles.css              # Custom styles + A4 print stylesheet
    └── js/
        ├── candidate_app.js        # Candidate registration, exam, timer, proctoring
        └── manager_app.js          # Manager dashboard, modals, charts, print engine
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** (tested on 3.13)
- **pip** package manager

### Installation

```bash
# 1. Navigate to the project directory
cd smarthire-finance

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Launch the application (auto-opens browser)
python run.py
```

The server starts at **http://127.0.0.1:8000** and automatically opens your default browser.

### First-Time Usage

1. **Candidate Flow**: Upload resume → Fill registration → Start 60-min assessment → Submit
2. **Manager Flow**: Click "Manager Login" → View candidate leaderboard → Click any candidate for full report → Print report

---

## 🧩 Question Engine & Composition

Every candidate receives **80 questions** in a **60-minute** timed session:

| Section                       | Count | Source                                   | Randomized? |
|:------------------------------|:------|:-----------------------------------------|:------------|
| **Indian Accounting (60%)**   | 48    | Sampled from 750-question finance pool   | ✅ Yes       |
| **IQ & Adaptability (20%)**   | 16    | Sampled from 250-question IQ pool        | ✅ Yes       |
| **Resume Verification (20%)**  | 16    | Dynamically generated from uploaded resume | ✅ Unique   |

### Question Categories (Finance 60%)
- GST Compliance (GSTR-1, GSTR-3B, GSTR-2B, ITC Reconciliation, E-Way Bills)
- TDS & TCS Taxation (Section 194C, 194J, 194Q, 206C, Form 26Q, Challan 281)
- Accounts Payable & P2P (3-Way Matching, PO-GRN-Invoice, Vendor Reconciliation)
- Accounts Receivable & O2C (Billing, Credit Notes, Debtors Aging)
- Banking & BRS (Bank Reconciliation, Cash Flow, NEFT/RTGS)
- Accounting Software (Tally Prime, Excel VLOOKUP, Pivot Tables)

### Banned Topics (Permanently Excluded)
WIP Valuation, BOM, SAP, Yield Tracking, Machine Hour Rates, Bank Drawing Power, Wizard Batch Runs, ISD, Form 3CD, EBITDA.

---

## 📄 Resume Parser & Domain Detection

The resume parser (`resume_parser.py`) intelligently extracts candidate information across multiple career domains:

### Extracted Entities
- **Identity**: Full Name, Email, Phone Number
- **Education**: Degree (B.Tech, B.Com, MBA, CA, MCA, etc.), CGPA/Percentage
- **Experience**: Years of experience (regex-extracted)
- **Domain Classification**: Auto-detects primary career domain

### Supported Domains & Skills

| Domain                    | Detected Skills                                                                          |
|:--------------------------|:-----------------------------------------------------------------------------------------|
| **AI & Machine Learning** | Computer Vision, YOLO, Deep Learning, CNNs, TensorFlow, Keras, PyTorch, OpenCV, NLP     |
| **Software Engineering**  | Python, SQL, Java, JavaScript, React, REST APIs, FastAPI, Git, Docker, AWS, C/C++        |
| **Finance & Accounting**  | GST, TDS/TCS, Accounts Payable, Accounts Receivable, BRS, Tally Prime, Excel            |

### Domain-Adaptive Verification Questions

| If Resume Domain Is...    | Verification Questions Cover...                                                           |
|:--------------------------|:------------------------------------------------------------------------------------------|
| **AI / Computer Vision**  | YOLO NMS, CNN Convolution Kernels, OpenCV BGR, TensorFlow Backpropagation, Precision/Recall |
| **Software Engineering**  | Python GIL, SQL Indexing, REST HTTP Codes, Git Merge vs Rebase, Docker vs VMs            |
| **Finance & Accounting**  | Rule 37 ITC Reversal, Section 194Q, 3-Way Matching, BRS Timing Differences               |

---

## 🔒 Proctoring Engine

The background proctoring system runs silently during the exam and logs the following events:

| Event Type              | Detection Method                   | Integrity Penalty |
|:------------------------|:-----------------------------------|:------------------|
| Tab Switch              | `document.visibilitychange` API    | −8 points         |
| Window Blur (Alt+Tab)   | `window.blur` event                | −8 points         |
| Fullscreen Exit         | `document.fullscreenchange` event  | −10 points        |
| Copy/Paste Attempt      | `copy` / `paste` event prevention  | −15 points        |
| Right-Click             | `contextmenu` event prevention     | Blocked           |

**Integrity Score** = `max(0, 100 − total_penalties)`

---

## 📊 Manager Dashboard & Hiring Intelligence

### 3-Tier Cognitive Breakdown

| Tier             | Focus Area                              | Passing Threshold |
|:-----------------|:----------------------------------------|:------------------|
| **Basic**        | Foundations & Daily Tasks               | ≥ 75% → Mastered  |
| **Intermediate** | Operational & Core Technical Knowledge  | ≥ 75% → Mastered  |
| **Advanced**     | Strategy, Controls & Architecture       | ≥ 70% → Mastered  |

### Cross-Role Placement Logic

| Performance Profile                                | Recommended Hiring Decision                                |
|:---------------------------------------------------|:-----------------------------------------------------------|
| Basic ≥ 75% + Intermediate ≥ 70% + Advanced ≥ 70% | ✅ **Great Fit for Finance Manager**                        |
| Basic ≥ 70% + Intermediate ≥ 60%                   | 🟡 **Hire as Accountant / Senior Accountant** (not Manager) |
| Basic ≥ 60%                                        | 🟠 **Junior / Entry-Level** (under supervision)             |
| Basic < 60%                                        | 🔴 **Do Not Hire** (fundamental gaps)                       |

### Manager Report Contents
1. **Overall Score** — Percentage with color-coded verdict badge
2. **Cognitive Tier Cards** — Basic / Intermediate / Advanced with progress bars
3. **Role Suitability Gauges** — Accountant, Senior Accountant, Finance Manager fit percentages
4. **6-Pillar Radar Chart** — AP/P2P, AR/O2C, GST/TDS, Inventory, Banking/MIS, IQ
5. **Topic-Wise Breakdown Table** — Category-level accuracy with color coding
6. **Resume vs. Reality Audit** — Skill verification with Pass/Fail indicators
7. **Proctoring Summary** — Tab switches, fullscreen exits, paste attempts, integrity score
8. **Suggested Interview Questions** — Auto-generated from candidate's weakest topics
9. **Printable Executive Report** — Multi-page A4 PDF with embedded chart snapshots

---

## 🔌 API Endpoints

### Candidate APIs

| Method | Endpoint                              | Description                                    |
|:-------|:--------------------------------------|:-----------------------------------------------|
| POST   | `/api/candidate/register`             | Register candidate with resume upload          |
| POST   | `/api/candidate/parse-resume-preview` | Instant resume parsing (returns extracted data) |

### Assessment APIs

| Method | Endpoint                                 | Description                              |
|:-------|:-----------------------------------------|:-----------------------------------------|
| GET    | `/api/assessment/{session_id}/start`     | Start exam, fetch 80 questions + timer   |
| POST   | `/api/assessment/{session_id}/autosave`  | Background auto-save answer              |
| POST   | `/api/assessment/{session_id}/submit`    | Final submission + score + report        |

### Manager APIs

| Method | Endpoint                                 | Description                              |
|:-------|:-----------------------------------------|:-----------------------------------------|
| GET    | `/api/manager/candidates`                | List all candidates with scores          |
| GET    | `/api/manager/report/{session_id}`       | Full hiring intelligence report (JSON)   |

### Proctoring APIs

| Method | Endpoint              | Description                              |
|:-------|:----------------------|:-----------------------------------------|
| POST   | `/api/proctoring/log` | Log proctoring event (tab, blur, etc.)   |

---

## 🗄 Database Schema

```
┌──────────────┐       ┌─────────────────────┐       ┌──────────────────┐
│  candidates  │       │ assessment_sessions  │       │ session_questions │
├──────────────┤       ├─────────────────────┤       ├──────────────────┤
│ id (PK)      │──┐    │ id (PK)             │──┐    │ id (PK)          │
│ full_name    │  │    │ candidate_id (FK) ◄─┘  │    │ session_id (FK)◄─┘
│ email        │  │    │ applied_role        │  │    │ question_number  │
│ phone        │  │    │ status              │  │    │ category         │
│ applied_role │  │    │ start_time          │  │    │ topic            │
│ experience   │  │    │ end_time            │  │    │ cognitive_level  │
│ resume_text  │  │    │ total_score         │  │    │ is_resume_based  │
│ skills       │  │    │ percentage          │  │    │ question_text    │
│ created_at   │  │    │ role_fit_verdict    │  │    │ option_a/b/c/d   │
└──────────────┘  │    │ integrity_score     │  │    │ correct_option   │
                  │    │ summary_report      │  │    │ selected_option  │
                  │    └─────────────────────┘  │    │ is_correct       │
                  │                             │    │ is_flagged       │
                  │    ┌─────────────────────┐  │    │ time_spent       │
                  │    │ proctoring_events   │  │    └──────────────────┘
                  │    ├─────────────────────┤  │
                  │    │ id (PK)             │  │
                  │    │ session_id (FK) ◄───┘
                  │    │ event_type          │
                  │    │ details             │
                  │    │ timestamp_seconds   │
                  │    └─────────────────────┘
```

---

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t smarthire-finance .
docker run -p 8000:8000 smarthire-finance
```

---

## 📜 License

This project is proprietary and built for internal recruitment assessment use.

---

## 👥 Credits

Built with ❤️ for Packaging & Manufacturing Finance Recruitment.
