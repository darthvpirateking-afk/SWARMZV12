# 🚀 NEXUSMON Deployment Guide

## Frontend Deployment (Vercel - Recommended)

### Option 1: Vercel (Fastest, Free)
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. From frontend/ directory
cd frontend
vercel --prod

# 3. Follow prompts:
# - Link to GitHub repo? y
# - Framework preset: Vite
# - Build command: npm run build
# - Output directory: dist
```

**Why Vercel?**
- ✅ Global CDN (blazing fast worldwide)
- ✅ Auto-builds from GitHub
- ✅ Free HTTPS + custom domains
- ✅ Perfect for React/Vite apps

---

## Backend Deployment 

### Option 1: Render.com (Best Balance)
```yaml
# render.yaml
services:
  - type: web
    name: nexusmon-backend
    runtime: python3
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python swarmz_server.py"
    envVars:
      - key: PORT
        value: 8000
```

**Deploy:**
```bash
# Connect GitHub repo to Render.com
# Auto-deploys on push to main
```

### Option 2: Fly.io (Fast Global)
```bash
# 1. Install Fly CLI
# 2. Login and launch
fly launch --name nexusmon-backend

# 3. Configure fly.toml:
app = "nexusmon-backend"
[build]
  builder = "paketobuildpacks/builder:base"
[http_service]
  internal_port = 8000
  auto_stop_machines = true
```

### Option 3: Railway (Current - Optimize)
```json
// railway.json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "variables": {
    "PORT": "8000",
    "NIXPACKS_INSTALL_CMD": "pip install -r requirements.txt"
  }
}
```

---

## Full Stack Deployment (Both Together)

### Recommended Architecture:
```
Frontend (Vercel)     Backend (Render/Fly)
├── Static React      ├── FastAPI Server
├── Global CDN        ├── Persistent compute  
├── Edge functions    ├── Database connections
└── Free tier         └── $5-10/month
```

### Environment Variables:
```bash
# Frontend (.env)
VITE_API_URL=https://nexusmon-backend.onrender.com

# Backend
DATABASE_URL=postgresql://...
ALLOWED_ORIGINS=https://nexusmon.vercel.app
```

---

## Performance Optimization

### Frontend:
```js
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          utils: ['uuid']
        }
      }
    }
  },
  server: {
    proxy: {
      "/v1": "https://nexusmon-backend.onrender.com"
    }
  }
})
```

### Backend:
```python
# Add to swarmz_server.py
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nexusmon.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Quick Deploy Commands

### Deploy Frontend to Vercel:
```bash
cd frontend && npx vercel --prod
```

### Deploy Backend to Render:
1. Connect GitHub repo to Render.com
2. Select "Web Service" 
3. Build: `pip install -r requirements.txt`
4. Start: `python swarmz_server.py`
5. Port: 8000

### Test Full Stack:
```bash
# Test connection
curl https://nexusmon-backend.onrender.com/health
```

**Result:** Sub-second load times globally! 🚀