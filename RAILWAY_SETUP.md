# 🚂 Quick Railway Setup

## 1️⃣ Deploy Backend

```bash
# In Railway dashboard:
1. New Project → Deploy from GitHub → Select SWARMZV12
2. Service auto-detected as Python
3. Add environment variables:
   - PYTHON_VERSION=3.13
   - PORT=8000
4. Copy your backend URL (e.g., https://swarmzv12-production.up.railway.app)
```

## 2️⃣ Deploy Frontend

```bash
# In same Railway project:
1. Click "New" → GitHub Repo → Select SWARMZV12 again
2. Settings → Root Directory: "frontend"
3. Add environment variable:
   - VITE_API_BASE_URL=<your-backend-url-from-step-1>
```

## 3️⃣ Update Local Config

```bash
# Update frontend/.env.production with your Railway backend URL
VITE_API_BASE_URL=https://your-actual-backend.up.railway.app
```

## 4️⃣ Commit and Push

```bash
git add railway.toml Procfile nixpacks.toml frontend/railway.toml frontend/nixpacks.toml
git add docs/RAILWAY_GUIDE.md RAILWAY_SETUP.md
git commit -m "feat(deploy): add Railway configuration"
git push
```

Railway will auto-deploy on push! 🚀

---

## 📖 Full Guide

See `docs/RAILWAY_GUIDE.md` for complete instructions, troubleshooting, and environment variables.

## ✅ Environment Variables to Set in Railway

### Backend Service
- `PYTHON_VERSION=3.13`
- `PORT=8000`

### Frontend Service  
- `VITE_API_BASE_URL=<your-backend-url>` ⚠️ **CRITICAL**

That's it! Railway handles the rest automatically.
