# Skill2Job — AI-Driven Placement Coordination & Skill Mapping System

<div align="center">

![Skill2Job Banner](https://img.shields.io/badge/Skill2Job-AI%20Placement%20System-4f46e5?style=for-the-badge&logo=graduation-cap)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql)

**An intelligent placement management platform that bridges students, placement officers, and companies using AI-powered skill matching, resume generation, and placement analytics.**

</div>

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Project](#running-the-project)
- [Default Accounts](#default-accounts)
- [API Overview](#api-overview)
- [Role-Based Access](#role-based-access)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [Contributing](#contributing)

---

## Overview

Skill2Job is a full-stack web application built as a Major Project for placement coordination. It uses **NLP**, **cosine similarity**, and **Random Forest ML** to:

- Match students to job roles based on skill vectors
- Generate AI-enhanced resumes tailored to dream jobs
- Identify skill gaps and recommend courses
- Predict placement success probability
- Give placement officers a complete dashboard to manage shortlisting, interviews, and placements

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SKILL2JOB SYSTEM                      │
├──────────────┬──────────────────────┬───────────────────┤
│   STUDENT    │  PLACEMENT OFFICER   │      ADMIN        │
│  INTERFACE   │     INTERFACE        │    INTERFACE      │
├──────────────┴──────────────────────┴───────────────────┤
│                  React + TypeScript (Vite)               │
├─────────────────────────────────────────────────────────┤
│                   Flask REST API (Python)                │
├──────────┬──────────┬──────────┬──────────┬────────────┤
│ Profile  │  Resume  │  Skill   │   Job    │ Analytics  │
│ Module   │  Module  │ Analysis │ Matching │  Module    │
├──────────┴──────────┴──────────┴──────────┴────────────┤
│         SpaCy NLP │ Scikit-learn │ ReportLab            │
├─────────────────────────────────────────────────────────┤
│                    MySQL Database                        │
└─────────────────────────────────────────────────────────┘
```

---

## Features

### Student Interface

| Feature           | Description                                                           |
| ----------------- | --------------------------------------------------------------------- |
| 🔐 Auth           | Register, login, forgot/reset password, JWT sessions                  |
| 👤 Profile        | Academic details, skills, projects, certifications                    |
| 📄 Resume         | Upload PDF/DOCX for NLP parsing, generate AI-enhanced PDF resume      |
| 🧠 Skill Analysis | Categorized skill breakdown with taxonomy matching                    |
| 💼 Job Matches    | Cosine similarity-based ranked job recommendations                    |
| 📊 Skill Gap      | Missing skills per job role with deficit scores                       |
| 📚 Courses        | Recommended courses (Coursera, Udemy, NPTEL, YouTube) per skill gap   |
| 🤖 AI Prediction  | Random Forest placement success probability with contributing factors |
| ⚙️ Settings       | Change password, notification preferences                             |

### Placement Officer Interface

| Feature          | Description                                                                   |
| ---------------- | ----------------------------------------------------------------------------- |
| 📋 Dashboard     | Placement overview, active jobs, recent shortlists, top skills demand         |
| 🏢 Companies     | Add and manage company records                                                |
| 💼 Job Roles     | Create job roles with auto skill vector generation                            |
| 👥 Shortlist     | Rank candidates by compatibility, mark shortlisted, send email alerts         |
| 🗓️ Interviews    | Schedule interviews, update status/result, auto-create placement on selection |
| 🎓 Placements    | Record confirmed placements with package details                              |
| 🔔 Notifications | Broadcast announcements to all students, shortlisted, or by department        |
| 📊 Analytics     | Placement stats, department/company breakdown, skill demand chart             |
| 📚 Courses       | Add course recommendations per skill                                          |

### Admin Interface

| Feature                 | Description                                                       |
| ----------------------- | ----------------------------------------------------------------- |
| 👥 User Management      | Create, search, paginate users; change roles; activate/deactivate |
| 🧠 Skill Taxonomy       | CRUD skill taxonomy with categories and synonyms                  |
| 📈 Placement Prediction | Train Random Forest model, batch predict all students             |
| 📊 Full Analytics       | All coordinator features + system health metrics                  |

---

## Tech Stack

| Layer          | Technology                                                   |
| -------------- | ------------------------------------------------------------ |
| **Frontend**   | React 18, TypeScript, Vite, React Router v6, Recharts, Axios |
| **Backend**    | Python 3.11, Flask 3.1, SQLAlchemy, Flask-Migrate            |
| **Database**   | MySQL 8.0 (PyMySQL driver)                                   |
| **ML / NLP**   | SpaCy (`en_core_web_sm`), Scikit-learn, NumPy                |
| **Auth**       | JWT (PyJWT), bcrypt                                          |
| **PDF**        | ReportLab (generation), PyPDF2 + python-docx (parsing)       |
| **Email**      | SMTP (Gmail/Outlook) with HTML templates                     |
| **Testing**    | Pytest, Hypothesis (property-based)                          |
| **Deployment** | Docker, Gunicorn, Nginx                                      |

---

## Project Structure

```
Skill2Job/
├── backend/                    # Flask API
│   ├── app/
│   │   ├── models/             # SQLAlchemy models
│   │   ├── routes/             # API blueprints
│   │   │   ├── auth_routes.py
│   │   │   ├── profile_routes.py
│   │   │   ├── skill_routes.py
│   │   │   ├── job_routes.py
│   │   │   ├── resume_routes.py
│   │   │   ├── dashboard_routes.py
│   │   │   ├── admin_routes.py
│   │   │   ├── interview_routes.py
│   │   │   ├── notification_routes.py
│   │   │   └── placement_routes.py
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── skill_analyzer.py
│   │   │   ├── job_matching.py
│   │   │   ├── ai_resume_service.py
│   │   │   ├── resume_generator.py
│   │   │   ├── resume_parser.py
│   │   │   ├── placement_predictor.py
│   │   │   ├── dashboard_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── email_service.py
│   │   │   └── job_role_knowledge_base.py
│   │   └── utils/              # Helpers
│   ├── tests/                  # Unit, integration, property tests
│   ├── uploads/                # Resume file storage
│   ├── config.py
│   ├── run.py
│   ├── seed.py                 # Seed admin + sample data
│   ├── seed_courses.py         # Seed course recommendations
│   └── requirements.txt
├── frontend/                   # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/
│   │   │   ├── student/        # Dashboard, Profile, Resume, Skills, Jobs, Settings
│   │   │   └── admin/          # Dashboard, Companies, Jobs, Shortlist, Interviews,
│   │   │                       # Placements, Notifications, Analytics, UserMgmt, etc.
│   │   ├── components/         # ProtectedRoute, Toast, LoadingSkeleton, SummaryCard
│   │   ├── context/            # AuthContext (JWT session management)
│   │   ├── services/           # Axios API client
│   │   └── styles/             # Global CSS design system
│   ├── package.json
│   └── vite.config.ts
├── database/
│   └── schema.sql              # Full MySQL schema (reference)
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## Prerequisites

Make sure you have the following installed:

| Tool    | Version | Download                         |
| ------- | ------- | -------------------------------- |
| Python  | 3.11+   | https://python.org               |
| Node.js | 18+     | https://nodejs.org               |
| MySQL   | 8.0+    | https://dev.mysql.com/downloads/ |
| Git     | Latest  | https://git-scm.com              |

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/PUNEETH1307/Skill-2-Job.git
cd Skill-2-Job
```

### 2. MySQL Database Setup

Open MySQL and create the database:

```sql
CREATE DATABASE skillbridge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> The tables are created automatically when you first run the backend.

### 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download SpaCy language model
python -m spacy download en_core_web_sm
```

Create your environment file:

```bash
# Copy the example file
cp .env.example .env
```

Edit `backend/.env` with your values:

```env
FLASK_CONFIG=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
JWT_TOKEN_EXPIRY_MINUTES=60

# Your MySQL credentials
DATABASE_URL=mysql+pymysql://root:yourpassword@127.0.0.1:3306/skillbridge

SPACY_MODEL=en_core_web_sm
UPLOAD_FOLDER=uploads
FRONTEND_URL=http://localhost:3000

# Optional: SMTP for emails (leave empty to log emails in dev)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@skillbridge.com
FROM_NAME=Skill2Job
```

Initialize the database tables:

```bash
python -c "
from app import create_app, db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('All tables created successfully!')
"
```

Seed initial data (skill taxonomy + sample courses):

```bash
python seed.py
python seed_courses.py
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install --ignore-scripts
node node_modules/esbuild/install.js

# Copy environment file
cp .env.example .env
```

The default `.env` is:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

---

## Running the Project

You need **two terminals** — one for the backend, one for the frontend.

### Terminal 1 — Backend (Flask)

```bash
cd backend
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

python run.py
```

Backend runs at: **http://localhost:5000**

### Terminal 2 — Frontend (Vite)

```bash
cd frontend
npm run dev
```

Frontend runs at: **http://localhost:3000**

> Open **http://localhost:3000** in your browser.

---

## Default Accounts

After running `seed.py`, the following accounts are created:

| Role                  | Email                     | Password       | Access                |
| --------------------- | ------------------------- | -------------- | --------------------- |
| **Admin**             | `admin@skillbridge.com`   | `Admin@1234`   | Full system access    |
| **Placement Officer** | `officer@skillbridge.com` | `Officer@1234` | Coordinator dashboard |
| **Student**           | `student@skillbridge.com` | `Student@1234` | Student dashboard     |

> **First time setup without seed:** Register at `/register` as a student, then use the setup endpoint to create your first admin:
>
> ```bash
> curl -X POST http://localhost:5000/api/auth/setup \
>   -H "Content-Type: application/json" \
>   -d '{"name":"Admin","email":"admin@example.com","password":"Admin@1234","role":"admin"}'
> ```
>
> After that, create more staff via **Admin Panel → User Management**.

---

## API Overview

All API routes are prefixed with `/api`.

| Module        | Base Path            | Description                                            |
| ------------- | -------------------- | ------------------------------------------------------ |
| Auth          | `/api/auth`          | Register, login, logout, password reset, role update   |
| Profile       | `/api/profile`       | Student profile CRUD                                   |
| Skills        | `/api/skills`        | Skill analysis                                         |
| Jobs          | `/api/jobs`          | Recommendations, skill gap, courses                    |
| Resume        | `/api/resume`        | Upload, parse, generate PDF                            |
| Dashboard     | `/api/dashboard`     | Role-specific summaries                                |
| Admin         | `/api/admin`         | Companies, jobs, shortlist, analytics, users, taxonomy |
| Interviews    | `/api/interviews`    | Schedule and manage interviews                         |
| Placements    | `/api/placements`    | Record confirmed placements                            |
| Notifications | `/api/notifications` | Send announcements                                     |

---

## Role-Based Access

```
Admin
  └── Full access to everything below +
      └── User Management (create/edit/role-change)
      └── Skill Taxonomy Management

Placement Officer
  └── Companies, Job Roles, Shortlisting
  └── Interviews, Placements, Notifications
  └── Analytics & Placement Prediction

Student
  └── Profile, Resume, Skill Analysis
  └── Job Recommendations, Skill Gap
  └── Course Recommendations, Settings
```

Login redirects automatically based on role:

- `student` → `/student/dashboard`
- `placement_officer` → `/admin/dashboard` (coordinator view)
- `admin` → `/admin/dashboard` (admin view)

---

## Environment Variables

### Backend (`backend/.env`)

| Variable                   | Required | Description                                        |
| -------------------------- | -------- | -------------------------------------------------- |
| `FLASK_CONFIG`             | Yes      | `development` / `production`                       |
| `SECRET_KEY`               | Yes      | Flask secret key                                   |
| `JWT_SECRET_KEY`           | Yes      | JWT signing key                                    |
| `JWT_TOKEN_EXPIRY_MINUTES` | No       | Token TTL (default: 60)                            |
| `DATABASE_URL`             | Yes      | MySQL connection string                            |
| `SPACY_MODEL`              | No       | SpaCy model (default: `en_core_web_sm`)            |
| `UPLOAD_FOLDER`            | No       | Resume upload path (default: `uploads`)            |
| `FRONTEND_URL`             | No       | For email links (default: `http://localhost:3000`) |
| `SMTP_HOST`                | No       | SMTP server (leave empty for dev logging)          |
| `SMTP_PORT`                | No       | SMTP port (default: 587)                           |
| `SMTP_USER`                | No       | SMTP username                                      |
| `SMTP_PASSWORD`            | No       | SMTP password                                      |

### Frontend (`frontend/.env`)

| Variable            | Required | Description                                            |
| ------------------- | -------- | ------------------------------------------------------ |
| `VITE_API_BASE_URL` | No       | Backend API URL (default: `http://localhost:5000/api`) |

---

## Database Schema

The full schema is in [`database/schema.sql`](database/schema.sql).

Key tables:

| Table                   | Description                                   |
| ----------------------- | --------------------------------------------- |
| `user`                  | All users (students, officers, admins)        |
| `student_profile`       | Academic details, skills JSON, skill vector   |
| `company`               | Company records                               |
| `job_role`              | Job positions with skill vectors              |
| `shortlist`             | Shortlisted candidates per job                |
| `interview`             | Interview scheduling and results              |
| `placement_record`      | Confirmed placements with package             |
| `skill_taxonomy`        | Canonical skills with categories and synonyms |
| `course_recommendation` | Courses mapped to skills                      |
| `notification`          | Sent announcements                            |
| `password_reset_token`  | Temporary reset tokens                        |

---

## Docker (Optional)

Run the full stack with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Stop
docker-compose down
```

---

## Running Tests

```bash
cd backend
venv\Scripts\activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is developed as a Major Project submission. All rights reserved.

---

<div align="center">
  Built with ❤️ by <strong>Puneeth J</strong> · <a href="https://github.com/PUNEETH1307">@PUNEETH1307</a>
</div>
