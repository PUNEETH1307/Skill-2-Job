# Skill2Job: AI-Driven Placement Coordination and Skill Mapping System

A production-ready, full-stack AI-powered web application that helps students, placement officers, and admins manage placement activities using Artificial Intelligence and Machine Learning.

---

## 1. Folder Structure

```
Skill2Job/
├── .github/workflows/ci.yml          # CI/CD pipeline (GitHub Actions)
├── frontend/                          # React + TypeScript Frontend
│   ├── src/
│   │   ├── components/                # Reusable UI components
│   │   │   ├── LoadingSkeleton.tsx     # Shimmer loading placeholders
│   │   │   ├── ProtectedRoute.tsx     # Auth guard with role hierarchy
│   │   │   └── SummaryCard.tsx        # Dashboard metric cards
│   │   ├── context/
│   │   │   └── AuthContext.tsx        # JWT session management
│   │   ├── pages/
│   │   │   ├── admin/                 # Admin/Officer modules
│   │   │   │   ├── Analytics.tsx      # Placement analytics + ML predictions
│   │   │   │   ├── Companies.tsx      # Company CRUD
│   │   │   │   ├── Courses.tsx        # Course management
│   │   │   │   ├── Dashboard.tsx      # Admin dashboard
│   │   │   │   ├── JobRoles.tsx       # Job openings management
│   │   │   │   ├── Shortlist.tsx      # AI candidate ranking
│   │   │   │   ├── SkillTaxonomy.tsx  # Skill taxonomy admin
│   │   │   │   └── UserManagement.tsx # User administration
│   │   │   ├── student/              # Student modules
│   │   │   │   ├── Dashboard.tsx      # Student dashboard
│   │   │   │   ├── JobRecommendations.tsx # AI job matches
│   │   │   │   ├── Profile.tsx        # Profile (upload resume OR manual)
│   │   │   │   ├── Resume.tsx         # AI resume generation + download
│   │   │   │   ├── SkillAnalysis.tsx  # NLP skill breakdown
│   │   │   │   └── SkillGap.tsx       # Gap analysis + course cards
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── ForgotPassword.tsx
│   │   │   └── ResetPassword.tsx
│   │   ├── services/
│   │   │   └── api.ts                 # Axios + JWT interceptors
│   │   ├── styles/                    # Modern CSS design system
│   │   │   ├── global.css             # Variables, animations, skeletons
│   │   │   ├── auth.css               # Glassmorphism auth pages
│   │   │   ├── dashboard.css          # Sidebar layout
│   │   │   └── pages.css              # Page components
│   │   ├── App.tsx                    # Router configuration
│   │   └── main.tsx                   # Entry point
│   ├── Dockerfile                     # Multi-stage production build
│   ├── nginx.conf                     # Production nginx config
│   ├── vercel.json                    # Vercel deployment config
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                           # Flask REST API
│   ├── app/
│   │   ├── models/
│   │   │   └── models.py             # SQLAlchemy entities (14 models)
│   │   ├── routes/
│   │   │   ├── admin_routes.py        # Admin APIs (1200+ lines)
│   │   │   ├── auth_routes.py         # Auth APIs
│   │   │   ├── dashboard_routes.py    # Dashboard + prediction APIs
│   │   │   ├── job_routes.py          # Recommendations + skill gap
│   │   │   ├── profile_routes.py      # Profile CRUD
│   │   │   ├── resume_routes.py       # Resume gen + upload + parse
│   │   │   └── skill_routes.py        # Skill analysis
│   │   ├── services/                  # Business logic + AI
│   │   │   ├── ai_resume_service.py   # NLP resume content generation
│   │   │   ├── analytics_service.py   # Placement analytics
│   │   │   ├── auth_service.py        # JWT + bcrypt + RBAC
│   │   │   ├── dashboard_service.py   # Dashboard aggregations
│   │   │   ├── job_matching.py        # Cosine similarity matching
│   │   │   ├── job_role_knowledge_base.py # Role-skill knowledge base
│   │   │   ├── placement_predictor.py # Random Forest ML predictions
│   │   │   ├── profile_service.py     # Profile management
│   │   │   ├── resume_generator.py    # PDF generation (ReportLab)
│   │   │   ├── resume_parser.py       # Resume text extraction (NLP)
│   │   │   └── skill_analyzer.py      # SpaCy skill extraction
│   │   ├── utils/
│   │   │   ├── auth_decorator.py      # @jwt_required, @role_required
│   │   │   ├── error_handlers.py      # Global error handling
│   │   │   └── sanitizer.py           # Input sanitization
│   │   └── __init__.py                # Flask app factory + CORS
│   ├── tests/                         # 418 tests
│   │   ├── unit/                      # 258 unit tests
│   │   ├── integration/               # 137 integration tests
│   │   └── property/                  # 23 property-based tests
│   ├── config.py                      # Dev/Test/Prod configurations
│   ├── gunicorn.conf.py               # Production WSGI config
│   ├── Procfile                       # Render/Railway start command
│   ├── requirements.txt               # Python dependencies
│   ├── run.py                         # Development entry point
│   ├── seed.py                        # DB seeding (taxonomy + admin)
│   └── seed_courses.py                # Course recommendations seeding
│
├── database/
│   ├── schema.sql                     # Complete MySQL schema (17 tables)
│   └── migrations/
│
├── Dockerfile                         # Backend Docker image
├── docker-compose.yml                 # Full stack orchestration
├── render.yaml                        # Render Blueprint
├── DEPLOYMENT.md                      # Deployment guide
└── README.md                          # This file
```

---

## 2. Source Code Summary

| Module | Technology | Lines | Description |
|--------|-----------|-------|-------------|
| Authentication | Flask + JWT + bcrypt | ~400 | Registration, login, logout, password reset, RBAC |
| Profile Management | Flask + SQLAlchemy | ~300 | CRUD with validation, resume upload auto-extraction |
| Skill Extraction | SpaCy NLP | ~250 | Tokenization, normalization, categorization, vectors |
| Job Matching | Scikit-learn | ~250 | Cosine similarity, recommendations, candidate ranking |
| Resume Generation | ReportLab + NLP | ~400 | AI-enhanced PDF with templates |
| Skill Gap Analysis | NumPy | ~100 | Vector comparison, deficit scoring |
| Course Recommendations | Content-based | ~50 | Skill-to-course mapping (49 courses, 4 providers) |
| Placement Prediction | Random Forest | ~200 | ML-based placement probability |
| Analytics | SQLAlchemy | ~150 | Department/company breakdowns, skill demand |
| Admin Dashboard | Flask + React | ~1500 | Full CRUD with search, filters, pagination |
| Frontend UI | React + TypeScript | ~3000 | Modern glassmorphism design, responsive |

---

## 3. API Documentation

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register student account |
| POST | `/api/auth/login` | Login → JWT token |
| POST | `/api/auth/logout` | Invalidate token |
| POST | `/api/auth/forgot-password` | Request reset token |
| POST | `/api/auth/reset-password` | Reset with token |

### Student Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/profile` | Get student profile |
| PUT | `/api/profile` | Create/update profile |

### Skills
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills/analysis` | Run NLP skill extraction |

### Jobs & Matching
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs/recommendations` | AI job recommendations (ranked) |
| GET | `/api/jobs/<id>/skill-gap` | Skill gap analysis |
| GET | `/api/jobs/<id>/courses` | Course recommendations for gaps |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/resume/generate` | Generate AI-enhanced PDF |
| GET | `/api/resume/download` | Download generated PDF |
| POST | `/api/resume/upload` | Upload existing resume |
| POST | `/api/resume/parse-for-profile` | Upload + auto-extract profile |
| GET | `/api/resume/uploads` | List uploaded resumes |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/student` | Student summary |
| GET | `/api/dashboard/coordinator` | Officer summary |
| GET | `/api/dashboard/admin` | Admin summary |
| GET | `/api/dashboard/student/prediction` | Placement probability |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users?search=&page=&per_page=` | List users (paginated) |
| POST | `/api/admin/users` | Create user |
| PUT | `/api/admin/users/<id>/status` | Activate/deactivate |
| GET/POST | `/api/admin/companies` | List/create companies |
| PUT | `/api/admin/companies/<id>` | Update company |
| POST | `/api/admin/jobs` | Create job role |
| PUT | `/api/admin/jobs/<id>` | Update job role |
| DELETE | `/api/admin/jobs/<id>` | Delete job role |
| GET | `/api/admin/jobs/<id>/shortlist` | Ranked candidates |
| POST | `/api/admin/jobs/<id>/shortlist` | Shortlist candidates |
| GET | `/api/admin/analytics?date_from=&date_to=` | Placement analytics |
| POST | `/api/admin/predictions/train` | Train ML model |
| GET | `/api/admin/predictions/batch` | All student predictions |
| GET/POST | `/api/admin/skills/taxonomy` | Skill taxonomy CRUD |
| GET/POST | `/api/admin/courses` | Course management |

---

## 4. Database Schema

17 tables in 3NF normalization. See `database/schema.sql` for full DDL.

**Core Entities:**
- `users` — Unified user table (student/admin/placement_officer)
- `students` — Academic profile + skill vectors
- `skills` — Canonical skill taxonomy with synonyms
- `student_skills` — Many-to-many junction with proficiency
- `companies` — Placement companies
- `job_roles` — Job openings with requirement vectors
- `applications` — Student applications with status tracking
- `resumes` — Generated and uploaded resumes
- `recommendations` — AI job recommendations with scores
- `courses` — Learning resources (Coursera/Udemy/NPTEL/YouTube)
- `skill_gaps` — Identified gaps with priority levels
- `analytics` — Event tracking for dashboards
- `placement_records` — Confirmed placements

---

## 5. Setup Guide

### Prerequisites
- Python 3.12+
- Node.js 18+
- MySQL (or SQLite for development)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python seed.py              # Creates tables + seeds taxonomy + admin
python seed_courses.py      # Seeds 49 courses from 4 providers
python run.py               # Starts on http://localhost:5000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev                 # Starts on http://localhost:3000
```

### Default Login
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@skill2job.com | Admin@123 |

---

## 6. Deployment Guide

See `DEPLOYMENT.md` for complete instructions. Three options:

1. **Render + Vercel** (free tier) — Recommended
2. **Railway** (all-in-one platform)
3. **Docker** (self-hosted VPS)

Quick Docker deploy:
```bash
docker-compose up -d --build
docker-compose exec backend python seed.py
docker-compose exec backend python seed_courses.py
```

---

## 7. Testing Guide

```bash
cd backend

# Run all tests (418 total)
python -m pytest tests/

# Unit tests only (258 tests, ~15s)
python -m pytest tests/unit/

# Integration tests (137 tests, ~90s)
python -m pytest tests/integration/

# Property-based tests (23 tests, ~30s)
python -m pytest tests/property/

# With coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Test Categories:**
- Unit: Auth, profile, skills, job matching, AI resume, dashboard, models
- Integration: All API endpoints via HTTP client
- Property: Hypothesis-based correctness proofs (score bounds, monotonicity, determinism)

---

## 8. Future Enhancements

### Short-term
- [ ] Email notifications (placement updates, password reset delivery)
- [ ] Real-time chat between students and placement officers (WebSocket)
- [ ] Resume templates selection (multiple PDF layouts)
- [ ] Bulk student import via CSV upload
- [ ] Interview scheduling module

### Medium-term
- [ ] Advanced ML: Collaborative filtering for job recommendations
- [ ] Resume parsing with LLM (GPT/Claude) for better extraction
- [ ] Video interview integration
- [ ] Company portal (self-service job posting)
- [ ] Mobile app (React Native)

### Long-term
- [ ] Multi-institution support (SaaS model)
- [ ] Blockchain-verified certifications
- [ ] AI mock interview with feedback
- [ ] Salary prediction model
- [ ] Alumni network integration
- [ ] Integration with LinkedIn/Naukri APIs

### Technical Improvements
- [ ] Redis caching for recommendations
- [ ] Celery task queue for async resume generation
- [ ] Elasticsearch for full-text search
- [ ] Rate limiting on auth endpoints
- [ ] Audit logging for admin actions
- [ ] Database read replicas for analytics queries

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, CSS Custom Properties |
| Backend | Python Flask, SQLAlchemy, Marshmallow |
| Database | SQLite (dev) / MySQL 8.0 (production) |
| AI/ML | SpaCy (NLP), Scikit-learn (cosine similarity, Random Forest) |
| PDF | ReportLab |
| Auth | JWT (PyJWT), bcrypt |
| Testing | Pytest, Hypothesis (property-based) |
| Deploy | Docker, Gunicorn, Nginx, GitHub Actions |

---

## License

This project is for educational and academic purposes.
