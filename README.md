<div align="center">

# 🎓 ExamMonitor

### Real-Time Online Exam Integrity Platform

[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Channels](https://img.shields.io/badge/Django_Channels-ASGI-ff6b35?style=for-the-badge)](https://channels.readthedocs.io)
[![Celery](https://img.shields.io/badge/Celery-Workers-37814A?style=for-the-badge&logo=celery)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-Message_Broker-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

**A production-grade exam proctoring system that monitors student behaviour in real time — no hardware required.**

[Features](#-features) · [Architecture](#-system-architecture) · [Tech Stack](#-tech-stack) · [Getting Started](#-getting-started) · [API Flow](#-data-flow) · [Screenshots](#-screenshots)

</div>

---

## 🧠 What is ExamMonitor?

ExamMonitor is a **full-stack Django web application** that enables institutions to conduct online exams with real-time integrity monitoring. Instead of requiring external proctoring software or webcam AI, it uses **browser event streams, WebSockets, and behavioural analysis** to detect and flag suspicious activity — all without leaving the browser.

> Built as a final year major project to demonstrate production-level backend engineering: real-time systems, async task queues, role-based access, and automated reporting.

---

## ✨ Features

### 👨‍🏫 For Examiners
- Create and manage exams with configurable trust thresholds
- Add MCQ, short answer, and long answer questions
- **Live dashboard** — watch all student sessions update in real time
- Instant email alert when a student is flagged
- View full session detail — every suspicious event with timestamps
- Download a professional **PDF integrity report** per student
- View **webcam snapshots** captured silently during the exam
- **Leaderboard** per exam with student rankings

### 👨‍🎓 For Students
- Clean, distraction-free exam interface with countdown timer
- Live integrity score bar showing session health
- Automatic exam submission when time expires
- **Result page** with score breakdown — correct/incorrect per question
- Exam leaderboard visibility after submission

### 🔍 Monitoring Engine
| Event | Penalty |
|-------|---------|
| Tab switch | −0.12 |
| Paste | −0.15 |
| Copy | −0.10 |
| Focus loss | −0.08 |
| Right click | −0.05 |
| Fast answer | −0.06 |

Trust score starts at **1.00** and decreases with each suspicious event. When it drops below the examiner-configured threshold, the session is flagged and an alert is fired instantly.

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser Layer                         │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Event Collector │  │   Exam UI    │  │  WebSocket    │  │
│  │  JS (tab/copy/  │  │  (timer,     │  │  Client       │  │
│  │  paste/blur)    │  │   questions) │  │               │  │
│  └────────┬────────┘  └──────────────┘  └───────┬───────┘  │
└───────────┼──────────────────────────────────────┼──────────┘
            │ Events                    WS + REST   │
┌───────────┼──────────────────────────────────────┼──────────┐
│           ▼         Django + Daphne (ASGI)        ▼          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  WS Consumer │  │  REST Views  │  │  Anomaly Engine   │  │
│  │  (Channels)  │  │  (Auth,Exam, │  │  Trust Score      │  │
│  │              │  │   Snapshot)  │  │  Recalculator     │  │
│  └──────┬───────┘  └──────────────┘  └─────────┬─────────┘  │
└─────────┼────────────────────────────────────────┼───────────┘
          │ Enqueue tasks              Broadcast    │
┌─────────┼────────────────────────────────────────┼───────────┐
│         ▼           Redis                         ▼           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Message Broker + Channel Layer              │ │
│  └──────────┬──────────────────────────┬──────────────────┘  │
│             │                          │                      │
│    ┌────────▼────────┐      ┌──────────▼────────┐            │
│    │  Celery Worker  │      │   Celery Beat      │            │
│    │  - Email alerts │      │  - Auto-submit     │            │
│    │  - PDF reports  │      │    every 60s       │            │
│    └─────────────────┘      └───────────────────┘            │
└──────────────────────────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────────────────┐
│                      Data Layer                               │
│                                                              │
│  ┌──────────────────┐   ┌──────────────────────────────────┐ │
│  │    PostgreSQL     │   │         Redis Cache              │ │
│  │  Users, Exams,   │   │   Live trust scores,             │ │
│  │  Sessions,       │   │   WebSocket channel layer        │ │
│  │  Events, Answers,│   │                                  │ │
│  │  Snapshots       │   └──────────────────────────────────┘ │
│  └──────────────────┘                                        │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### Real-Time Monitoring Pipeline

```
Student switches tab
        │
        ▼
JS visibilitychange event fires
        │
        ▼
WebSocket sends → { type: "tab_switch", metadata: {} }
        │
        ▼
Django Channels consumer receives
        │
        ├──► Save SuspiciousEvent to PostgreSQL
        │
        ├──► Recalculate trust score
        │         penalty = Σ EVENT_WEIGHTS[event_type]
        │         score   = max(0.0, 1.0 - penalty)
        │
        ├──► If score < threshold → flag session
        │         └──► Celery fires send_flag_alert.delay()
        │                   └──► Email sent to examiner
        │
        └──► Broadcast to examiner dashboard via Redis group
                  └──► Dashboard WS receives update
                            └──► Trust bar animates in real time
```

### Snapshot Pipeline

```
Every 30 seconds (hidden from student)
        │
        ▼
JS captures webcam frame via Canvas API
        │
        ▼
Base64 JPEG → POST /monitor/session/{id}/snapshot/
        │
        ▼
Django saves ExamSnapshot to DB
        │
        ▼
Examiner views snapshots grid in session detail
```

---

## 🗄 Database Schema

```
User (AbstractUser)
├── role: student | examiner
│
├──── Exam
│     ├── created_by → User
│     ├── duration_mins
│     ├── trust_threshold
│     └── shuffle_questions
│           │
│           └──── Question
│                 ├── exam → Exam
│                 ├── question_type: mcq | short | long
│                 ├── options (JSON)
│                 └── correct_answer
│
└──── ExamSession
      ├── student → User
      ├── exam → Exam
      ├── trust_score (float)
      ├── status: active | submitted | flagged
      │
      ├──── SuspiciousEvent
      │     ├── session → ExamSession
      │     ├── event_type
      │     ├── severity: low | med | high
      │     └── metadata (JSON)
      │
      ├──── Answer
      │     ├── session → ExamSession
      │     ├── question → Question
      │     └── response
      │
      └──── ExamSnapshot
            ├── session → ExamSession
            └── image (base64 TextField)
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | Django 5.x | Views, ORM, Auth, Admin |
| **ASGI Server** | Daphne | WebSocket + HTTP handling |
| **Real-Time** | Django Channels | WebSocket consumers |
| **Message Broker** | Redis | Channel layer + Celery broker |
| **Task Queue** | Celery | Async email alerts |
| **Scheduler** | Celery Beat | Auto-submit on timer expiry |
| **Database** | PostgreSQL | Primary data store |
| **PDF Generation** | ReportLab | Integrity reports |
| **Email** | Gmail SMTP | Examiner alerts |
| **Frontend** | Vanilla JS + CSS variables | No framework needed |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Redis
- PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/rajmohan-14/exam-integrity-monitor.git
cd exam-integrity-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and email credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Running the Application

You need **3 terminal windows**:

```bash
# Terminal 1 — Web server (ASGI + WebSocket)
daphne -p 8000 exammonitor.asgi:application

# Terminal 2 — Celery worker (background tasks)
celery -A exammonitor worker --loglevel=info

# Terminal 3 — Celery Beat (scheduled tasks)
celery -A exammonitor beat --loglevel=info
```

Visit **http://127.0.0.1:8000**

### Environment Variables

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/exammonitor
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## 📁 Project Structure

```
exam-integrity-monitor/
├── exammonitor/              # Project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py               # ASGI + Channels routing
│   └── celery.py             # Celery app
│
├── users/                    # Authentication app
│   ├── models.py             # Custom User with role field
│   └── views.py              # Login, signup, logout
│
├── exams/                    # Exam management app
│   ├── models.py             # Exam, Question
│   ├── views.py              # Create, edit, delete exams
│   └── forms.py              # ExamForm, QuestionForm
│
└── monitoring/               # Core monitoring app
    ├── models.py             # ExamSession, SuspiciousEvent,
    │                         # Answer, ExamSnapshot
    ├── consumers.py          # WebSocket consumers
    │                         # (ExamConsumer, DashboardConsumer)
    ├── tasks.py              # Celery tasks
    │                         # (send_flag_alert, auto_submit)
    ├── views.py              # Dashboard, results, PDF, snapshots
    └── routing.py            # WebSocket URL patterns
```

---

## 🔑 Key Engineering Decisions

### Why ASGI over WSGI?
Django's default `runserver` uses WSGI — a synchronous protocol that closes connections after each response. WebSockets require **persistent connections**. Switching to ASGI with Daphne enables handling HTTP and WebSocket connections simultaneously in the same process.

### Why Celery for email alerts?
Sending an email inside a WebSocket consumer would block the entire async event loop until the SMTP server responds. By offloading to Celery, the consumer stays non-blocking — it queues the task in Redis and returns in microseconds while the Celery worker handles the slow I/O independently.

### Why base64 for snapshots?
Avoiding filesystem dependencies keeps the application stateless and deploy-friendly. Base64-encoded images stored in PostgreSQL are immediately portable — no S3 bucket, no media server configuration needed to get the project running.

### Trust score algorithm
```python
EVENT_WEIGHTS = {
    'tab_switch': 0.12,
    'paste':      0.15,   # highest — likely pasting an answer
    'copy':       0.10,
    'focus_loss': 0.08,
    'right_click':0.05,
    'fast_answer':0.06,
}

def recalculate(session):
    events  = SuspiciousEvent.objects.filter(session=session)
    penalty = sum(EVENT_WEIGHTS.get(e.event_type, 0.05) for e in events)
    return round(max(0.0, 1.0 - penalty), 2)
```

Score starts at `1.0` and decays cumulatively — a student who pastes twice and switches tabs once has a score of `1.0 - 0.15 - 0.15 - 0.12 = 0.58`. Examiners configure the threshold per exam.

---

## 📊 Features Demo Flow

```
1. Examiner signs up → creates exam → adds questions
                                │
2. Student signs up → sees exam list → clicks Start
                                │
3. Exam page loads:
   ├── Webcam stream starts (silent snapshots every 30s)
   ├── Countdown timer begins
   └── WebSocket connects to monitoring pipeline
                                │
4. Student switches tab ────────┤
   └── trust: 1.00 → 0.88      │
       ┌── examiner dashboard   │
       └── bar animates live ───┘
                                │
5. Score drops below threshold (0.5)
   └── Session flagged
       └── Email fires → examiner inbox
                                │
6. Student submits (or timer auto-submits)
   └── Result page: score, correct/incorrect, integrity score
                                │
7. Examiner views session detail
   ├── Full event log with timestamps
   ├── Webcam snapshot grid
   └── Download PDF report
```

---

## 🧪 What I Learned

This project was built phase by phase as a learning exercise. Key concepts implemented from scratch:

- **Django ORM** — complex querysets, `select_related`, `prefetch_related`, `update_or_create`
- **ASGI / Django Channels** — writing async WebSocket consumers, channel groups, Redis channel layers
- **Celery** — `@shared_task`, `.delay()`, periodic tasks with Celery Beat
- **Template inheritance** — DRY base layout with `{% block %}` system
- **Custom decorators** — role-based access control beyond `@login_required`
- **ReportLab** — programmatic PDF generation with tables, styles, and dynamic content
- **Browser APIs** — `visibilitychange`, `getUserMedia`, Canvas API for webcam snapshots

---

## 🗺 Future Roadmap

- [ ] Face detection using `face-api.js` (flag if no face or multiple faces detected)
- [ ] Django REST Framework API + React frontend
- [ ] Prometheus + Grafana observability dashboard
- [ ] Docker Compose for one-command setup
- [ ] GitHub Actions CI/CD pipeline
- [ ] S3 storage for webcam snapshots

---

## 👨‍💻 Author

**Raj Mohan**
Information Science & Engineering, SJB Institute of Technology

[![GitHub](https://img.shields.io/badge/GitHub-rajmohan--14-181717?style=flat&logo=github)](https://github.com/rajmohan-14)

---

<div align="center">

**Built with Django · Channels · Celery · Redis · PostgreSQL**

*A real-time system built to learn — every line written, debugged, and understood.*

</div>
