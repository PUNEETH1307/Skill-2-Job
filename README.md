# Skill2Job — AI-Driven Placement Coordination & Skill Mapping System

<div align="center">

![Skill2Job Banner](https://img.shields.io/badge/Skill2Job-AI%20Placement%20System-4f46e5?style=for-the-badge&logo=graduation-cap)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?style=flat-square&logo=typescript)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql)

**An intelligent placement management platform that bridges students, placement officers, and companies using AI-powered skill matching, resume generation, and placement analytics.**

[Features](#features) · [Quick Start](#quick-start) · [API](#api-overview) · [Deployment](#deployment) · [Contributing](#contributing)

</div>

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Running the Project](#running-the-project)
- [Default Accounts](#default-accounts)
- [API Overview](#api-overview)
- [Role-Based Access](#role-based-access)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [Deployment](#deployment)
- [Running Tests](#running-tests)
- [Operational Notes](#operational-notes)
- [Contributing](#contributing)

---

## Overview

Skill2Job is a full-stack web application built as a Major Project for placement coordination. It uses **NLP**, **cosine similarity**, and **Random Forest ML** to:

- Match students to job roles based on skill vectors
- Generate AI-enhanced resumes tailored to dream jobs
- Identify skill gaps and recommend courses
- Predict placement success probability
- Give placement officers a complete dashboard to manage shortlisting, interviews, and placements
- Support placement drives with eligibility checks, registration, attendance verification, and missed-drive blocking
- Provide dream-job tracking, hiring updates, notifications, interview schedules, and placement history

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

| Feature             | Description                                                           |
| ------------------- | --------------------------------------------------------------------- |
| 🔐 Auth             | Register, login, forgot/reset password, JWT sessions                  |
| 👤 Profile          | Academic details, skills, projects, certifications                    |
| 📄 Resume           | Upload PDF/DOCX for NLP parsing, generate AI-enhanced PDF resume      |
| 🧠 Skill Analysis   | Categorized skill breakdown with taxonomy matching                    |
| 💼 Job Matches      | Cosine similarity-based ranked job recommendations                    |
| 📊 Skill Gap        | Missing skills per job role with deficit scores                       |
| 📚 Courses          | Recommended courses (Coursera, Udemy, NPTEL, YouTube) per skill gap   |
| 🤖 AI Prediction    | Random Forest placement success probability with contributing factors |
| 🎯 Dream Jobs       | Save up to three target roles with AI match scores and skill gaps     |
| 📡 Hiring Updates   | View live job links and preparation resources for saved dream jobs    |
| 🗓️ Placement Drives | Check eligibility, register, verify attendance, and track status      |
| 🔔 Notifications    | Read placement announcements and interview/placement updates          |
| 🗣️ Interviews       | View scheduled interviews, results, and meeting details               |
| 📈 Placement Stats  | View placement history and cross-role statistics                      |
| ⚙️ Settings         | Change password, notification preferences                             |

### Placement Officer Interface

| Feature             | Description                                                                   |
| ------------------- | ----------------------------------------------------------------------------- |
| 📋 Dashboard        | Placement overview, active jobs, recent shortlists, top skills demand         |
| 🏢 Companies        | Add and manage company records                                                |
| 💼 Job Roles        | Create job roles with auto skill vector generation                            |
| 👥 Shortlist        | Rank candidates by compatibility, mark shortlisted, send email alerts         |
| 🗓️ Interviews       | Schedule interviews, update status/result, auto-create placement on selection |
| 🎓 Placements       | Record confirmed placements with package details                              |
| 🔔 Notifications    | Broadcast announcements to all students, shortlisted, or by department        |
| 🗓️ Placement Drives | Create drives, define eligibility, manage registration and attendance         |
| 📊 Analytics        | Placement stats, department/company breakdown, skill demand chart             |
| 📚 Courses          | Add course recommendations per skill                                          |
| 📈 Statistics       | View placement summaries and student outcomes                                 |
| ⚙️ Settings         | Manage account settings                                                       |

### Admin Interface

| Feature                 | Description                                                       |
| ----------------------- | ----------------------------------------------------------------- |
| 👥 User Management      | Create, search, paginate users; change roles; activate/deactivate |
| 🧠 Skill Taxonomy       | CRUD skill taxonomy with categories and synonyms                  |
| 📈 Placement Prediction | Train Random Forest model, batch predict all students             |
| 📊 Full Analytics       | All coordinator features + system health metrics                  |

### Core Workflows

1. **Student career preparation:** register → complete profile → upload or parse a resume → analyze skills → review job matches → inspect skill gaps → follow recommended courses.
2. **Dream-job planning:** select a company and active role → save up to three Dream Jobs → review the AI match score and missing skills → open hiring links and preparation resources → remove or replace saved targets.
3. **Placement-drive participation:** view eligible drives → register before the deadline → verify attendance with the drive code → track registration and attendance status. Missed eligible registrations can temporarily block future registrations.
4. **Placement coordination:** create companies and roles → define eligibility → publish drives → review eligible and ineligible students → filter and paginate candidates → shortlist students → schedule interviews → record results and confirmed placements.
5. **Administration:** manage users and roles → maintain the skill taxonomy and synonyms → add course recommendations → train or run placement predictions → review analytics and statistics.

### Platform Capabilities

- JWT authentication with role-based access for students, placement officers, and administrators
- Skill taxonomy normalization with categories, synonyms, and vector-based matching
- PDF/DOCX resume parsing and generated PDF resumes with selectable templates
- Resume upload history, download, preview, profile autofill, and profile-photo support
- Cosine-similarity job recommendations, skill-gap analysis, and course recommendations
- Company-specific Dream Jobs with a three-role limit, AI match scoring, missing-skill analysis, hiring links, and preparation resources
- Random Forest placement prediction with contributing factors
- Placement-drive rules for minimum CGPA, graduation year, backlog requirements, registration deadlines, attendance codes, and missed-drive blocking
- Interview scheduling, status/result tracking, email alerts, confirmed placements, and placement history
- Search, filtering, and pagination for operational student and candidate lists
- Optional SMTP notifications; development mode logs email content when SMTP is not configured

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
│   ├── seed_all.py             # Seed a complete demonstration dataset
│   ├── migrations/             # Tracked SQL schema changes
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

## Quick Start

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
# Windows PowerShell
Copy-Item .env.example .env
# Git Bash / macOS / Linux
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

# Windows PowerShell
Copy-Item .env.example .env
# Git Bash / macOS / Linux
cp .env.example .env
```

The default `.env` is:

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

For a fuller demonstration dataset, run `python seed_all.py` from `backend` instead of `seed.py` and `seed_courses.py`.

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

After running `seed.py`, the following account is created:

| Role      | Email                 | Password    | Access             |
| --------- | --------------------- | ----------- | ------------------ |
| **Admin** | `admin@skill2job.com` | `Admin@123` | Full system access |

For demo users, run `seed_all.py`:

| Role    | Email                      | Password       |
| ------- | -------------------------- | -------------- |
| Admin   | `sysadmin@skillbridge.com` | `SysAdmin1234` |
| Admin   | `admin@skillbridge.com`    | `Admin1234`    |
| Student | `teststudent@test.com`     | `Test@1234`    |

Change all seeded passwords before using the application outside local development.

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

| Module        | Base Path            | Description                                                                 |
| ------------- | -------------------- | --------------------------------------------------------------------------- |
| Auth          | `/api/auth`          | Register, login, logout, password reset, role update                        |
| Profile       | `/api/profile`       | Student profile CRUD                                                        |
| Skills        | `/api/skills`        | Skill analysis                                                              |
| Jobs          | `/api/jobs`          | Recommendations, skill gap, courses                                         |
| Resume        | `/api/resume`        | Upload, parse, generate PDF                                                 |
| Dashboard     | `/api/dashboard`     | Role-specific summaries                                                     |
| Admin         | `/api/admin`         | Companies, jobs, shortlist, analytics, users, taxonomy, courses, prediction |
| Interviews    | `/api/interviews`    | Schedule and manage interviews                                              |
| Placements    | `/api/placements`    | Placement records and placement-drive management                            |
| Notifications | `/api/notifications` | Send and receive announcements                                              |
| Statistics    | `/api/stats`         | Cross-role placement statistics                                             |

### Important Endpoint Groups

| Area                   | Endpoints                                                                                            | Purpose                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Authentication         | `/api/auth/register`, `/login`, `/logout`, `/forgot-password`, `/reset-password`, `/change-password` | Account lifecycle, JWT sessions, and password management                                   |
| Student profile        | `/api/profile/profile`, `/api/profile/profile/photo`                                                 | Academic profile, skills, projects, certifications, and profile photo                      |
| Skill analysis         | `/api/skills/analysis`                                                                               | Normalize and categorize profile skills and generate skill insights                        |
| Job matching           | `/api/jobs/recommendations`                                                                          | Ranked job-role recommendations based on skill compatibility                               |
| Dream Jobs             | `/api/jobs/options`, `/api/jobs/dream-jobs`, `/api/jobs/dream-jobs/updates`                          | Select target roles, save up to three, calculate match gaps, and retrieve hiring resources |
| Skill gaps and courses | `/api/jobs/<id>/skill-gap`, `/api/jobs/<id>/courses`                                                 | Explain missing skills and return learning recommendations                                 |
| Resumes                | `/api/resume/parse-for-profile`, `/upload`, `/uploads`, `/generate`, `/download`, `/preview`         | Parse, store, list, generate, download, and preview resumes                                |
| Dashboards             | `/api/dashboard/student`, `/coordinator`, `/admin`, `/student/prediction`                            | Role-specific summaries and placement prediction                                           |
| Companies and roles    | `/api/admin/companies`, `/api/admin/jobs`                                                            | Manage employers and job roles                                                             |
| Shortlisting           | `/api/admin/jobs/<id>/shortlist`                                                                     | Rank candidates and manage job shortlists                                                  |
| Drives                 | `/api/placements/drives`, `/api/placements/drive-management`                                         | Student registration and officer drive management                                          |
| Interviews             | `/api/interviews`, `/api/interviews/my`                                                              | Schedule, update, delete, and view interviews                                              |
| Notifications          | `/api/notifications`, `/api/notifications/student`                                                   | Broadcast and retrieve notifications                                                       |
| Placements             | `/api/placements`, `/api/placements/my`                                                              | Create, update, delete, and view placement records                                         |
| Admin tools            | `/api/admin/users`, `/api/admin/skills/taxonomy`, `/api/admin/courses`, `/api/admin/predictions/*`   | User management, taxonomy, courses, and ML prediction operations                           |

Protected endpoints require the JWT returned by `/api/auth/login`. Access is restricted by role where indicated in the route implementation.

### Frontend Route Map

| Area                        | Routes                                                                                                                                                                                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Public                      | `/`, `/login`, `/register`, `/forgot-password`, `/reset-password`                                                                                                                                                                                          |
| Student                     | `/student/dashboard`, `/student/profile`, `/student/skills`, `/student/jobs`, `/student/dream-jobs`, `/student/drives`, `/student/jobs/:id/gap`, `/student/resume`, `/student/settings`, `/student/notifications`, `/student/interviews`, `/student/stats` |
| Placement officer and admin | `/admin/dashboard`, `/admin/companies`, `/admin/jobs`, `/admin/shortlist`, `/admin/analytics`, `/admin/courses`, `/admin/interviews`, `/admin/notifications`, `/admin/placements`, `/admin/drives`, `/admin/stats`, `/admin/settings`                      |
| Admin only                  | `/admin/users`, `/admin/skills`                                                                                                                                                                                                                            |

---

## Role-Based Access

```
Admin
  └── Full access to everything below +
      └── User Management (create/edit/role-change)
      └── Skill Taxonomy Management

Placement Officer
  └── Companies, Job Roles, Shortlisting
  └── Placement Drives, Interviews, Placements, Notifications
  └── Courses, Analytics, Statistics & Placement Prediction

Student
  └── Profile, Resume, Skill Analysis
  └── Job Recommendations, Dream Jobs, Hiring Updates, Skill Gap
  └── Courses, Placement Drives, Interviews, Notifications, Statistics
  └── Settings and password management
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
| `CORS_ORIGINS`             | No       | Comma-separated allowed frontend origins           |
| `SMTP_HOST`                | No       | SMTP server (leave empty for dev logging)          |
| `SMTP_PORT`                | No       | SMTP port (default: 587)                           |
| `SMTP_USER`                | No       | SMTP username                                      |
| `SMTP_PASSWORD`            | No       | SMTP password                                      |
| `FROM_EMAIL`               | No       | Sender email address                               |
| `FROM_NAME`                | No       | Sender display name                                |

### Frontend (`frontend/.env`)

| Variable            | Required | Description                                            |
| ------------------- | -------- | ------------------------------------------------------ |
| `VITE_API_BASE_URL` | No       | Backend API URL (default: `http://localhost:5000/api`) |

---

## Database Schema

The reference schema is in [`database/schema.sql`](database/schema.sql). For local development, the application creates its SQLAlchemy tables with `db.create_all()` during setup. Keep `DATABASE_URL` and the database name consistent with the environment you are running; Docker Compose uses `skill2job`, while the example local connection string uses `skillbridge`.

Key tables:

| Table                   | Description                                    |
| ----------------------- | ---------------------------------------------- |
| `user`                  | All users (students, officers, admins)         |
| `student_profile`       | Academic details, skills JSON, skill vector    |
| `company`               | Company records                                |
| `job_role`              | Job positions with skill vectors               |
| `dream_job`             | Student-specific saved target roles            |
| `placement_drive`       | Drive dates, eligibility rules, and attendance |
| `drive_registration`    | Student registration and attendance status     |
| `drive_shortlist`       | Drive-specific candidate shortlist             |
| `shortlist`             | Shortlisted candidates per job                 |
| `interview`             | Interview scheduling and results               |
| `placement_record`      | Confirmed placements with package              |
| `skill_taxonomy`        | Canonical skills with categories and synonyms  |
| `course_recommendation` | Courses mapped to skills                       |
| `notification`          | Sent announcements                             |
| `resume_upload`         | Uploaded resume metadata and file history      |
| `password_reset_token`  | Temporary reset tokens                         |

---

## Deployment

### Docker Compose

Run the full stack with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Stop
docker-compose down
```

The Compose stack starts MySQL, the Gunicorn backend, and the Nginx-served frontend. Copy the root `.env.example` to `.env` first and replace the development secrets before exposing the stack publicly.

### Render + Vercel

The repository also includes a deployment guide for hosting the backend on Render, the frontend on Vercel, and MySQL on a managed provider:

- [DEPLOYMENT.md](DEPLOYMENT.md)
- [render.yaml](render.yaml)
- [frontend/vercel.json](frontend/vercel.json)

Configure `VITE_API_BASE_URL` on Vercel and `CORS_ORIGINS` / `FRONTEND_URL` on the backend with the deployed frontend origin.

---

## Running Tests

```bash
cd backend
venv\Scripts\activate

# Run all tests
pytest

# Run with coverage (install pytest-cov separately if needed)
python -m pytest --cov=app tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

Frontend checks:

```bash
cd frontend
npm run build
npm run lint
```

---

## Operational Notes

- Resume uploads accept PDF and DOCX files and are limited to 10 MB. Uploaded resumes, generated resumes, and profile photos are stored under the configured `UPLOAD_FOLDER`.
- SMTP is optional. When SMTP credentials are empty in development, email content is logged instead of delivered.
- The backend initializes Flask-Migrate and supports `db.create_all()` for first-time local setup. Use the SQL files under `database/migrations/` for tracked schema changes in environments that require migration control.
- Automated tests use an in-memory SQLite database through the testing configuration; normal development and deployment use MySQL.
- Local-disk uploads are not durable on ephemeral hosting. Use persistent storage or object storage for production resume and profile-photo retention.
- Replace development secrets, seeded passwords, and default database credentials before deployment. Set `FLASK_CONFIG=production`, `CORS_ORIGINS`, and `FRONTEND_URL` for a deployed frontend.

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
