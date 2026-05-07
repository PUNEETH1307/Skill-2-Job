# Skill2Job Placement System

A full-stack web application that connects students with job opportunities through intelligent skill matching, resume generation, and placement analytics.

## Features

### Student Portal
- **Profile Management** — Academic details, skills, projects, and certifications
- **Skill Analysis** — Categorized skill breakdown with taxonomy-based classification
- **Job Recommendations** — AI-powered job matching with compatibility scores
- **Resume Generator** — Auto-generated professional resumes in PDF format
- **Dashboard** — Profile completeness, skill summary, top job matches, and quick actions

### Coordinator Portal (Placement Officer)
- **Placement Analytics** — Overview stats, department breakdowns, skill demand analysis
- **Company Management** — Add, edit, and manage registered companies
- **Job Role Management** — Create roles with skill requirements and eligibility criteria
- **Candidate Shortlisting** — View eligible candidates and manage shortlists
- **Dashboard** — Placement overview, recent shortlists, in-demand skills, and quick actions

### Admin Portal
- **User Management** — Create accounts, manage roles, activate/deactivate users
- **Skill Taxonomy** — Manage canonical skills, categories, deprecation, and uncategorized terms
- **System Overview** — User counts, taxonomy health, placement statistics
- **Dashboard** — System-wide metrics, taxonomy health indicators, and admin quick actions

## Tech Stack

### Backend
- **Python 3.12** with **Flask** web framework
- **SQLAlchemy** ORM with SQLite (development)
- **JWT** authentication with role-based access control
- **Hypothesis** for property-based testing

### Frontend
- **React 18** with **TypeScript**
- **Vite** build tool
- **React Router** for client-side routing
- **Axios** for API communication
- **Recharts** for data visualization

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # Flask blueprints (API endpoints)
│   │   ├── services/        # Business logic layer
│   │   └── utils/           # Auth decorators, error handlers, sanitizer
│   ├── tests/
│   │   ├── integration/     # API endpoint tests
│   │   ├── property/        # Hypothesis property-based tests
│   │   └── unit/            # Unit tests for services
│   ├── config.py            # App configuration
│   ├── run.py               # Entry point
│   └── seed.py              # Database seeder
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── context/         # React context (Auth)
│   │   ├── pages/           # Page components (student/, admin/)
│   │   ├── services/        # API client
│   │   └── styles/          # CSS stylesheets
│   └── index.html
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python seed.py      # Seed the database with sample data
python run.py       # Starts Flask server on http://localhost:5000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev         # Starts Vite dev server on http://localhost:3000
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Property-based tests only
python -m pytest tests/property/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v
```

## Default Credentials (after seeding)

| Role              | Email                | Password     |
|-------------------|----------------------|--------------|
| Admin             | admin@skill2job.com  | admin123     |
| Placement Officer | officer@skill2job.com| officer123   |
| Student           | student@skill2job.com| student123   |

## API Endpoints

### Authentication
- `POST /api/auth/register` — Register new user
- `POST /api/auth/login` — Login and receive JWT token

### Dashboard
- `GET /api/dashboard/student` — Student dashboard summary
- `GET /api/dashboard/coordinator` — Coordinator dashboard summary
- `GET /api/dashboard/admin` — Admin dashboard summary

### Profiles
- `GET /api/profile` — Get student profile
- `PUT /api/profile` — Update student profile

### Skills
- `GET /api/skills/analyze` — Analyze student skills
- `GET /api/skills/taxonomy` — Get skill taxonomy

### Jobs
- `GET /api/jobs` — List job roles
- `GET /api/jobs/recommendations` — Get job recommendations

### Admin
- `GET /api/admin/users` — List users
- `POST /api/admin/users` — Create user
- `GET /api/admin/analytics` — Placement analytics

## License

This project is developed as a Major Project for academic purposes.
