# 🚀 Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Already installed as a dev dependency in `frontend/`
3. **GitHub Repo**: Your code is already pushed to `https://github.com/dclawstack/dclaw-crisis`

---

## Option A: Deploy via Vercel CLI (Recommended for first setup)

### Step 1: Login to Vercel

```bash
cd frontend
npx vercel login
```
Follow the browser prompt to authenticate.

### Step 2: Link & Deploy

```bash
npx vercel --prod
```

This will:
- Create a new Vercel project linked to your frontend directory
- Build and deploy your Next.js app
- Provide you with a production URL (e.g., `https://dclaw-crisis-xxx.vercel.app`)

### Step 3: Set Environment Variables

In the Vercel dashboard (or via CLI):

```bash
npx vercel env add NEXT_PUBLIC_API_URL production
# Enter your backend API URL, e.g.:
# https://api.yourdomain.com
```

Or set it in the [Vercel Dashboard → Project → Settings → Environment Variables](https://vercel.com/dashboard).

### Step 4: Re-deploy

```bash
npx vercel --prod
```

---

## Option B: GitHub Integration (Auto-deploy on push)

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repo: `dclawstack/dclaw-crisis`
3. **Root Directory**: Set to `frontend`
4. **Framework Preset**: Next.js
5. Add environment variable: `NEXT_PUBLIC_API_URL` = your backend URL
6. Deploy

Every push to `main` will auto-deploy.

---

## Backend Deployment (FastAPI)

The backend is a FastAPI app that needs to be deployed separately. Recommended platforms:

| Platform | Why |
|----------|-----|
| **Railway** | `railway.app` — easiest Postgres + FastAPI deploy |
| **Render** | `render.com` — free tier available |
| **Fly.io** | `fly.io` — Docker-based, great for FastAPI |
| **AWS / GCP** | For production scale |

### Quick: Railway Deploy

```bash
cd backend
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
railway add --database postgres
railway up
```

Set `DATABASE_URL` in Railway environment variables.

---

## Project Structure for Vercel

```
frontend/          ← Vercel deploys from here
├── src/
│   ├── app/
│   │   ├── page.tsx          ← Marketing landing page
│   │   ├── dashboard/        ← App dashboard
│   │   ├── crisis/           ← Crisis management
│   │   ├── team/             ← Team members
│   │   ├── action-items/     ← Action item kanban
│   │   └── playbooks/        ← Response playbooks
│   ├── components/ui/        ← Pre-built UI components
│   └── lib/api.ts            ← API client
├── vercel.json               ← Rewrites + headers
└── next.config.js            ← Next.js config

backend/           ← Deploy separately (Railway/Render/Fly)
├── app/
│   ├── api/v1/               ← All API routers
│   ├── models/               ← SQLAlchemy models
│   └── core/                 ← Config + database
├── alembic/                  ← Migrations
└── Dockerfile                ← Container image
```

---

## Environment Variables

### Frontend (Vercel)

| Variable | Example | Required |
|----------|---------|----------|
| `NEXT_PUBLIC_API_URL` | `https://api.dclaw-crisis.com` | Yes for app pages |

### Backend (Railway/Render/Fly)

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host/db` | Yes |
| `APP_ENV` | `production` | Yes |
| `SECRET_KEY` | `your-secret-key` | Yes |

---

## Post-Deploy Checklist

- [ ] Frontend landing page loads at Vercel URL
- [ ] Dashboard page loads (`/dashboard`)
- [ ] All app pages navigable (`/crisis`, `/team`, `/action-items`, `/playbooks`)
- [ ] Backend API responds with `{"status":"ok"}` at `/health/`
- [ ] `NEXT_PUBLIC_API_URL` is set and frontend can reach backend (CORS enabled)
- [ ] Database migrations have run (`alembic upgrade head`)

---

## Troubleshooting

### "API not found" on Vercel
Make sure `NEXT_PUBLIC_API_URL` points to your deployed backend, not `localhost`.

### CORS errors
Backend CORS is configured to allow `*` origins in `app/api/main.py`. For production, restrict to your Vercel domain:
```python
allow_origins=["https://your-vercel-domain.vercel.app"]
```

### Build fails on Vercel
Check that `frontend/package.json` has `tailwindcss-animate` in `dependencies` (not `devDependencies`).

---

## Need Help?

- Vercel Docs: [vercel.com/docs](https://vercel.com/docs)
- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Next.js on Vercel: [nextjs.org/docs/deployment](https://nextjs.org/docs/deployment)
