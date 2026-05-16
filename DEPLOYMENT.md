# Skill2Job — Deployment Guide

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Vercel/       │────▶│   Render/        │────▶│   MySQL Cloud   │
│   Netlify       │     │   Railway        │     │   (PlanetScale/ │
│   (Frontend)    │     │   (Backend)      │     │    Aiven/AWS)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
     React SPA           Flask + Gunicorn          Persistent DB
```

---

## Option 1: Render (Backend) + Vercel (Frontend)

### Backend — Render

1. **Create a Render account** at https://render.com

2. **Connect your GitHub repo** and create a new Web Service:
   - Root Directory: `backend`
   - Runtime: Python 3
   - Build Command:
     ```bash
     pip install -r requirements.txt && pip install gunicorn && python -m spacy download en_core_web_sm
     ```
   - Start Command:
     ```bash
     gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app
     ```

3. **Set environment variables** on Render:
   ```
   FLASK_CONFIG=production
   SECRET_KEY=<generate-random-64-char-string>
   JWT_SECRET_KEY=<generate-random-64-char-string>
   JWT_TOKEN_EXPIRY_MINUTES=60
   DATABASE_URL=mysql+pymysql://user:pass@host:3306/skill2job
   SPACY_MODEL=en_core_web_sm
   ```

4. **Create a MySQL database** (Render offers PostgreSQL free; for MySQL use PlanetScale or Aiven):
   - PlanetScale: https://planetscale.com (free tier)
   - Aiven: https://aiven.io (free trial)
   - Run `database/schema.sql` against your cloud DB

5. **Seed the database**:
   ```bash
   # From Render shell or locally with DATABASE_URL set
   python seed.py
   python seed_courses.py
   ```

### Frontend — Vercel

1. **Create a Vercel account** at https://vercel.com

2. **Import your repo** and set:
   - Framework: Vite
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Set environment variable**:
   ```
   VITE_API_BASE_URL=https://your-backend.onrender.com/api
   ```

4. **Update `frontend/src/services/api.ts`** for production:
   ```typescript
   baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'
   ```

5. **Deploy** — Vercel auto-deploys on push to main.

---

## Option 2: Railway (Full Stack)

1. **Create a Railway account** at https://railway.app

2. **Create a new project** from your GitHub repo

3. **Add a MySQL service** from Railway's marketplace

4. **Add the backend service**:
   - Root: `/backend`
   - Start: `gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 run:app`
   - Variables: Same as Render above (Railway auto-provides `DATABASE_URL`)

5. **Add the frontend service**:
   - Root: `/frontend`
   - Build: `npm run build`
   - Serve the `dist/` folder with a static file server

---

## Option 3: Docker (Self-hosted / VPS)

```bash
# Clone the repo
git clone https://github.com/your-repo/skill2job.git
cd skill2job

# Create .env file
cp .env.example .env
# Edit .env with your production secrets

# Build and start all services
docker-compose up -d --build

# Seed the database
docker-compose exec backend python seed.py
docker-compose exec backend python seed_courses.py

# Access the app
# Frontend: http://localhost:80
# Backend API: http://localhost:5000
```

---

## Environment Variables Reference

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_CONFIG` | Yes | `production` |
| `SECRET_KEY` | Yes | Random 64-char string for Flask sessions |
| `JWT_SECRET_KEY` | Yes | Random 64-char string for JWT signing |
| `JWT_TOKEN_EXPIRY_MINUTES` | No | Token lifetime (default: 30) |
| `DATABASE_URL` | Yes | MySQL connection string |
| `SPACY_MODEL` | No | SpaCy model name (default: `en_core_web_sm`) |
| `UPLOAD_FOLDER` | No | File upload directory (default: `uploads`) |
| `PORT` | No | Server port (default: 5000, auto-set by Render/Railway) |

### Frontend

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Backend API URL (e.g., `https://api.skill2job.com/api`) |

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push:

1. **Backend Tests** — Unit, integration, and property-based tests
2. **Frontend Build** — TypeScript check + Vite build
3. **Deploy** (main branch only) — Auto-deploys to Render + Vercel

### Required GitHub Secrets

| Secret | Service |
|--------|---------|
| `RENDER_SERVICE_ID` | Render backend service ID |
| `RENDER_API_KEY` | Render API key |
| `VERCEL_TOKEN` | Vercel deployment token |
| `VERCEL_ORG_ID` | Vercel organization ID |
| `VERCEL_PROJECT_ID` | Vercel project ID |

---

## Database Migration (Production)

```bash
# Connect to your cloud MySQL and run:
mysql -h <host> -u <user> -p <database> < database/schema.sql

# Or via the backend container:
docker-compose exec backend python seed.py
```

---

## SSL/HTTPS

- **Vercel**: Automatic SSL on custom domains
- **Render**: Automatic SSL on `.onrender.com` and custom domains
- **Railway**: Automatic SSL
- **Docker/VPS**: Use Caddy or nginx with Let's Encrypt

---

## Monitoring

- **Render**: Built-in logs and metrics
- **Railway**: Built-in observability
- **Self-hosted**: Add Sentry for error tracking:
  ```bash
  pip install sentry-sdk[flask]
  ```
