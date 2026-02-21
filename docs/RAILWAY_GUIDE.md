# 🚂 SWARMZ Railway Deployment Guide

## Quick Start

Railway auto-detects your project and deploys both backend and frontend. Follow these steps:

---

## 🎯 Step 1: Deploy Backend (Python)

### Create Backend Service

1. Go to your Railway dashboard: https://railway.app/dashboard
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your `SWARMZV12` repository
4. Railway will detect the Python app automatically

### Configure Backend Environment Variables

In the Railway dashboard for your backend service, add these variables:

```bash
# Required
PYTHON_VERSION=3.13
PORT=8000

# Optional (for enhanced features)
OPERATOR_KEY=your-secure-operator-key-here
SWARMZ_LOG_LEVEL=INFO
ENABLE_REALITY_GATE=true
ENABLE_MISSION_CONTRACT=true
ENABLE_LEAD_AUDIT=true
```

### Get Your Backend URL

After deployment, Railway gives you a public URL like:
- `https://swarmzv12-production.up.railway.app`
- Or custom domain: `api.yourdomain.com`

**Copy this URL** - you'll need it for the frontend!

---

## 🎨 Step 2: Deploy Frontend (React/Vite)

### Create Frontend Service

1. In the **same Railway project**, click **"New"** → **"GitHub Repo"**
2. Select your `SWARMZV12` repository again
3. Railway will ask which service to deploy

### Configure Root Directory

Railway needs to know the frontend is in a subdirectory:

1. Go to **Settings** tab
2. Under **Build & Deploy**, set:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: Leave empty (uses nixpacks.toml)

### Configure Frontend Environment Variables

In the Railway dashboard for your frontend service, add:

```bash
# CRITICAL: Set your backend URL here
VITE_API_BASE_URL=https://swarmzv12-production.up.railway.app

# Optional
VITE_OPERATOR_KEY=your-operator-key-if-needed
```

**Replace the URL** with your actual backend URL from Step 1!

---

## 🔗 Step 3: Connect Services (Optional but Recommended)

Railway lets you connect services with private networking:

1. In your backend service, go to **"Variables"** tab
2. Note the **Service Variables** like `${{RAILWAY_PRIVATE_DOMAIN}}`
3. You can use private URLs instead of public for better performance

---

## 🧪 Step 4: Test Deployment

### Test Backend
```bash
# Health check
curl https://your-backend.up.railway.app/health

# Should return: {"status":"ok"}

# API docs
open https://your-backend.up.railway.app/docs
```

### Test Frontend
1. Open your frontend URL: `https://your-frontend.up.railway.app`
2. Open browser DevTools (F12) → Network tab
3. Check that API calls go to your backend URL
4. Verify no CORS errors

---

## 📦 Project Structure on Railway

After setup, you should have **ONE Railway project** with **TWO services**:

```
My SWARMZ Project
├── swarmz-backend (Python)
│   ├── Root: /
│   ├── Start: python run_server.py
│   └── URL: https://swarmzv12-production.up.railway.app
│
└── swarmz-frontend (Node.js/Static)
    ├── Root: /frontend
    ├── Start: serve -s dist
    └── URL: https://swarmzv12-frontend.up.railway.app
```

---

## 🗄️ Step 5: Add Database (Optional)

If you need Postgres:

1. In your Railway project, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway auto-provisions and connects it
3. Get connection string from Variables tab: `${{DATABASE_URL}}`
4. Add to backend environment variables:
   ```bash
   DATABASE_URL=${{DATABASE_URL}}
   ```

---

## 🔧 Configuration Files Created

### Backend
- ✅ `railway.toml` - Railway configuration
- ✅ `Procfile` - Process definition
- ✅ `nixpacks.toml` - Build configuration

### Frontend  
- ✅ `frontend/railway.toml` - Frontend configuration
- ✅ `frontend/nixpacks.toml` - Frontend build config
- ✅ `frontend/.env.production` - Production environment

---

## 🚀 Deployment Commands

Railway deploys automatically on `git push`. To manually deploy:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy backend
railway up

# Deploy frontend (from frontend directory)
cd frontend
railway up
```

---

## 🐛 Troubleshooting

### Frontend Can't Connect to Backend

**Symptom**: Network errors, CORS errors, or "Failed to fetch"

**Solution**:
1. Check `VITE_API_BASE_URL` in frontend environment variables
2. Verify backend URL is correct (no trailing slash)
3. Test backend health endpoint directly
4. Check Railway logs for backend errors

### Build Failures

**Backend**:
- Check Python version is 3.13
- Verify `requirements.txt` is in root
- Check Railway build logs

**Frontend**:
- Verify Root Directory is set to `frontend`
- Check `package.json` has `build` script
- Ensure environment variables are set **before** build

### Port Issues

Railway automatically sets `$PORT`. Don't hardcode ports!

**Backend**: Uses `$PORT` from environment
**Frontend**: Vite dev server uses port from Railway

### Database Connection

If using Postgres:
1. Verify `DATABASE_URL` environment variable exists
2. Check Railway's DB service is running
3. Look for connection errors in logs
4. Ensure `scripts/init_db.py` runs successfully

---

## 💰 Railway Pricing

- **Free Tier**: $5 credit/month (enough for development)
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage

**Tip**: Use sleep mode for dev environments to save credits

---

## 🎯 Environment Variables Summary

### Backend Service
```bash
# Required
PYTHON_VERSION=3.13
PORT=8000

# Your backend URL (for reference)
RAILWAY_PUBLIC_DOMAIN=swarmzv12-production.up.railway.app

# Optional
OPERATOR_KEY=your-operator-key
DATABASE_URL=${{DATABASE_URL}}
SWARMZ_LOG_LEVEL=INFO
```

### Frontend Service
```bash
# CRITICAL: Must match your backend URL
VITE_API_BASE_URL=https://swarmzv12-production.up.railway.app

# Optional
VITE_OPERATOR_KEY=your-operator-key
```

---

## 📚 Additional Resources

- [Railway Docs](https://docs.railway.app/)
- [Nixpacks Docs](https://nixpacks.com/docs)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [Custom Domains](https://docs.railway.app/deploy/exposing-your-app)

---

## ✅ Checklist

- [ ] Backend deployed and health check passes
- [ ] Frontend deployed and loads
- [ ] `VITE_API_BASE_URL` set correctly
- [ ] API calls work (check DevTools Network tab)
- [ ] No CORS errors
- [ ] Optional: Database connected
- [ ] Optional: Custom domain configured

---

## 🎉 Success!

Once both services are green in Railway:
1. Open your frontend URL
2. You should see the SWARMZ UI
3. All API calls should work
4. Check Railway logs to monitor activity

**Your SWARMZ is now live!** 🚂✨
