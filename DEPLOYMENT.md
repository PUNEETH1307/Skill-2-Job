# Skill2Job — Deployment Guide

## Architecture

```
Browser
  │
  ▼
┌─────────────────────┐        ┌──────────────────────┐        ┌──────────────────┐
│      Vercel         │──API──▶│      Render.com      │──DB──▶│     Aiven.io     │
│   (React Frontend)  │        │   (Flask Backend)    │        │  (MySQL Cloud)   │
│   skill2job.vercel  │        │  skill2job.onrender  │        │  Free 5GB MySQL  │
│   .app  — FREE      │        │  .com  — FREE        │        │  — FREE          │
└─────────────────────┘        └──────────────────────┘        └──────────────────┘
```

**All three services are FREE.** Users register → data is stored in Aiven MySQL → accessible from anywhere.

---

## Step 1 — Set Up Aiven MySQL (Cloud Database)

1. Go to **https://aiven.io** → Sign up (free, no credit card needed for free trial)

2. Click **Create Service** → Choose **MySQL**

3. Select:
   - Plan: **Free** (or Hobbyist)
   - Cloud: **AWS** → Region: **us-east-1** (or closest to you)
   - Service name: `skill2job-db`

4. Wait ~2 minutes for it to provision

5. Click your service → go to **Overview** tab → copy the **Service URI**
   It looks like:
   ```
   mysql://avnadmin:YOURPASSWORD@mysql-skill2job-xxx.aivencloud.com:PORT/defaultdb?ssl-mode=REQUIRED
   ```

6. Go to **Databases** tab → Create a new database named `skillbridge`

7. Your final connection string will be:
   ```
   mysql+pymysql://avnadmin:YOURPASSWORD@mysql-skill2job-xxx.aivencloud.com:PORT/skillbridge?ssl_ca=/etc/ssl/certs/ca-certificates.crt
   ```
   > **Save this** — you'll need it for Render.

8. Go to **CA Certificate** tab → Download the CA cert (needed for SSL)

---

## Step 2 — Deploy Backend on Render

1. Go to **https://render.com** → Sign up with GitHub

2. Click **New** → **Web Service**

3. Connect your GitHub repo: `PUNEETH1307/Skill-2-Job`

4. Configure:
   | Setting | Value |
   |---|---|
   | **Name** | `skill2job-backend` |
   | **Root Directory** | `backend` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt && python -m spacy download en_core_web_sm` |
   | **Start Command** | `gunicorn --config gunicorn.conf.py run:app` |
   | **Plan** | Free |

5. Click **Advanced** → **Add Environment Variables**:

   | Key | Value |
   |---|---|
   | `FLASK_CONFIG` | `production` |
   | `DATABASE_URL` | *(your Aiven MySQL URI from Step 1)* |
   | `SECRET_KEY` | *(click Generate)* |
   | `JWT_SECRET_KEY` | *(click Generate)* |
   | `JWT_TOKEN_EXPIRY_MINUTES` | `60` |
   | `SPACY_MODEL` | `en_core_web_sm` |
   | `CORS_ORIGINS` | `https://your-app.vercel.app` *(update after Step 3)* |
   | `FRONTEND_URL` | `https://your-app.vercel.app` *(update after Step 3)* |

6. Click **Create Web Service** → wait for build (~5 min)

7. Once deployed, your backend URL will be:
   ```
   https://skill2job-backend.onrender.com
   ```

8. **Initialize the database** — open Render **Shell** tab and run:
   ```bash
   python -c "
   from app import create_app, db
   app = create_app('production')
   with app.app_context():
       db.create_all()
       print('Tables created!')
   "
   ```

9. **Seed initial data**:
   ```bash
   python seed.py
   python seed_courses.py
   ```

10. **Create your first admin** via Render Shell:
    ```bash
    curl -X POST https://skill2job-backend.onrender.com/api/auth/setup \
      -H "Content-Type: application/json" \
      -d '{"name":"Admin","email":"admin@yourdomain.com","password":"YourPassword@123","role":"admin"}'
    ```

---

## Step 3 — Deploy Frontend on Vercel

1. Go to **https://vercel.com** → Sign up with GitHub

2. Click **Add New** → **Project**

3. Import your repo: `PUNEETH1307/Skill-2-Job`

4. Configure:
   | Setting | Value |
   |---|---|
   | **Framework Preset** | `Vite` |
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm run build` |
   | **Output Directory** | `dist` |

5. **Environment Variables**:
   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://skill2job-backend.onrender.com/api` |

6. Click **Deploy** → wait ~2 min

7. Your frontend URL will be:
   ```
   https://skill-2-job.vercel.app
   ```

---

## Step 4 — Connect Frontend ↔ Backend

1. Go back to **Render** → your backend service → **Environment**

2. Update these two variables with your actual Vercel URL:
   ```
   CORS_ORIGINS = https://skill-2-job.vercel.app
   FRONTEND_URL = https://skill-2-job.vercel.app
   ```

3. Click **Save Changes** → Render auto-redeploys

4. Test the connection:
   ```
   https://skill-2-job.vercel.app  →  opens the app
   https://skill2job-backend.onrender.com/api/auth/login  →  returns JSON
   ```

---

## Step 5 — Verify Everything Works

Open your Vercel URL and test:

- [ ] Register a new student account
- [ ] Login → redirects to student dashboard
- [ ] Complete profile → skills show in Skill Analysis
- [ ] Login as admin → admin dashboard loads
- [ ] Admin → User Management → users visible

---

## Auto-Deploy on Push

Both Vercel and Render watch your GitHub repo. Every time you push to `main`:
- Vercel rebuilds the frontend automatically
- Render rebuilds the backend automatically

---

## Free Tier Limits

| Service | Limit | Impact |
|---|---|---|
| Render (free) | Spins down after 15 min inactivity | First request after idle takes ~30 sec to wake up |
| Aiven (free trial) | 30 days, then needs upgrade | Use Clever Cloud or PlanetScale for permanent free MySQL |
| Vercel (free) | 100GB bandwidth/month | More than enough |

### Permanent Free MySQL Alternatives

If Aiven trial expires, use one of these:

**Option A — Clever Cloud (permanent free MySQL)**
1. Go to https://clever-cloud.com → Sign up
2. Create → MySQL addon → Free plan (256MB)
3. Copy the connection string → update `DATABASE_URL` on Render

**Option B — PlanetScale (permanent free)**
1. Go to https://planetscale.com → Sign up
2. Create database → Connect → copy connection string
3. Note: PlanetScale uses a different SSL setup — add `?ssl=true` to URL

---

## Troubleshooting

**Backend not starting on Render:**
- Check Render logs → look for `ModuleNotFoundError`
- Make sure `requirements.txt` has `cryptography==44.0.2` for MySQL SSL

**CORS error in browser:**
- Make sure `CORS_ORIGINS` on Render exactly matches your Vercel URL (no trailing slash)

**Database connection error:**
- Aiven requires SSL — make sure your `DATABASE_URL` includes `?ssl_ca=...` or use `?ssl=true`
- Test locally: `mysql -h <host> -P <port> -u avnadmin -p skillbridge`

**Render free tier cold start:**
- First request after 15 min idle takes ~30 seconds
- Upgrade to Render Starter ($7/month) to avoid this

**SpaCy model not found:**
- Build command must include `python -m spacy download en_core_web_sm`
- Check Render build logs to confirm it downloaded

---

## Custom Domain (Optional)

**Vercel:**
1. Vercel Dashboard → your project → Settings → Domains
2. Add your domain → follow DNS instructions

**Render:**
1. Render Dashboard → your service → Settings → Custom Domains
2. Add domain → update CORS_ORIGINS to match

---

## Summary

| What | Where | URL |
|---|---|---|
| Frontend | Vercel | `https://skill-2-job.vercel.app` |
| Backend API | Render | `https://skill2job-backend.onrender.com` |
| Database | Aiven | MySQL cloud (not publicly accessible) |
