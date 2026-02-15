#!/usr/bin/env python3
"""
SWARMZ Web Server - PWA-enabled REST API

A FastAPI-based web server that exposes SWARMZ capabilities via REST API
and serves a Progressive Web App for mobile-friendly access.
"""

import os
import socket
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from swarmz import SwarmzCore


# API Models
class TaskExecuteRequest(BaseModel):
    task: str
    params: Dict[str, Any] = {}


class TaskExecuteResponse(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="SWARMZ API",
    description="Operator-Sovereign 'Do Anything' System - REST API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/docs/openapi.json"
)

# Initialize SWARMZ core
swarmz = SwarmzCore()

# Load plugins on startup
plugins_dir = Path(__file__).parent / "plugins"
if plugins_dir.exists():
    for plugin_file in plugins_dir.glob("*.py"):
        if plugin_file.name != "__init__.py":
            try:
                swarmz.load_plugin(str(plugin_file))
                print(f"✓ Loaded plugin: {plugin_file.stem}")
            except Exception as e:
                print(f"✗ Failed to load plugin {plugin_file.stem}: {e}")


# Helper function to get LAN IP
def get_lan_ip():
    """Get the LAN IP address of this machine."""
    try:
        # Create a socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"


# PWA Home Page HTML
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the PWA home page."""
    lan_ip = get_lan_ip()
    port = os.environ.get("PORT", "8000")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SWARMZ - Operator-Sovereign Do Anything System">
    <meta name="theme-color" content="#6366f1">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="SWARMZ">
    <title>SWARMZ - Operator-Sovereign System</title>
    <link rel="manifest" href="/manifest.webmanifest">
    <link rel="icon" type="image/svg+xml" href="/icon.svg">
    <link rel="apple-touch-icon" href="/apple-touch-icon.svg">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 1rem;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            padding: 2rem 0;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .subtitle {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .card h2 {{
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        .link-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        .link-btn {{
            display: block;
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 0.5rem;
            padding: 1rem;
            text-decoration: none;
            color: #fff;
            text-align: center;
            transition: all 0.3s;
        }}
        .link-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }}
        .link-btn .icon {{
            font-size: 2rem;
            display: block;
            margin-bottom: 0.5rem;
        }}
        .info-box {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }}
        .install-banner {{
            background: rgba(34, 197, 94, 0.3);
            border: 2px solid rgba(34, 197, 94, 0.5);
            border-radius: 0.5rem;
            padding: 1rem;
            margin: 1rem 0;
            display: none;
        }}
        .install-banner.show {{
            display: block;
        }}
        .install-btn {{
            background: #22c55e;
            border: none;
            border-radius: 0.5rem;
            padding: 0.75rem 1.5rem;
            color: #fff;
            font-weight: bold;
            cursor: pointer;
            margin-top: 0.5rem;
        }}
        footer {{
            text-align: center;
            padding: 2rem 0;
            opacity: 0.8;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ SWARMZ</h1>
            <p class="subtitle">Operator-Sovereign "Do Anything" System</p>
        </header>

        <div class="install-banner" id="installBanner">
            <strong>📱 Install SWARMZ as an app!</strong>
            <p>Add to your home screen for quick access and offline capabilities.</p>
            <button class="install-btn" id="installButton">Install App</button>
        </div>

        <div class="card">
            <h2>🌐 Access URLs</h2>
            <div class="info-box">
                <strong>Local:</strong> http://localhost:{port}<br>
                <strong>LAN:</strong> http://{lan_ip}:{port}
            </div>
            <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.9;">
                💡 Use the LAN URL to access SWARMZ from other devices on your network
            </p>
        </div>

        <div class="card">
            <h2>🔗 Quick Links</h2>
            <div class="link-grid">
                <a href="/docs" class="link-btn">
                    <span class="icon">📚</span>
                    API Docs
                </a>
                <a href="/v1/tasks" class="link-btn">
                    <span class="icon">📋</span>
                    List Tasks
                </a>
                <a href="/v1/health" class="link-btn">
                    <span class="icon">💚</span>
                    Health Check
                </a>
                <a href="/v1/audit" class="link-btn">
                    <span class="icon">🔍</span>
                    Audit Log
                </a>
            </div>
        </div>

        <div class="card">
            <h2>🎯 Core Principles</h2>
            <ul style="line-height: 2; padding-left: 1.5rem;">
                <li><strong>Operator Sovereignty</strong> - You maintain complete control</li>
                <li><strong>Extensibility</strong> - Plugin-based architecture</li>
                <li><strong>Transparency</strong> - All actions are logged</li>
                <li><strong>Flexibility</strong> - "Do anything" philosophy</li>
            </ul>
        </div>

        <footer>
            <p>SWARMZ v1.0.0 | MIT License</p>
        </footer>
    </div>

    <script>
        // Service Worker Registration
        if ('serviceWorker' in navigator) {{
            navigator.serviceWorker.register('/sw.js')
                .then(reg => console.log('Service Worker registered:', reg))
                .catch(err => console.error('Service Worker registration failed:', err));
        }}

        // PWA Install Prompt
        let deferredPrompt;
        const installBanner = document.getElementById('installBanner');
        const installButton = document.getElementById('installButton');

        window.addEventListener('beforeinstallprompt', (e) => {{
            e.preventDefault();
            deferredPrompt = e;
            installBanner.classList.add('show');
        }});

        installButton.addEventListener('click', async () => {{
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            const {{ outcome }} = await deferredPrompt.userChoice;
            console.log('Install prompt outcome:', outcome);
            deferredPrompt = null;
            installBanner.classList.remove('show');
        }});

        window.addEventListener('appinstalled', () => {{
            console.log('PWA installed successfully');
            installBanner.classList.remove('show');
        }});
    </script>
</body>
</html>"""
    return html


# PWA Manifest
@app.get("/manifest.webmanifest")
async def manifest():
    """Serve the PWA manifest."""
    manifest_data = {
        "name": "SWARMZ - Operator-Sovereign System",
        "short_name": "SWARMZ",
        "description": "Operator-Sovereign 'Do Anything' System - Execute tasks with complete control",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#667eea",
        "theme_color": "#6366f1",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/icon.svg",
                "type": "image/svg+xml",
                "sizes": "any",
                "purpose": "any maskable"
            },
            {
                "src": "/apple-touch-icon.svg",
                "type": "image/svg+xml",
                "sizes": "180x180"
            }
        ],
        "categories": ["productivity", "utilities", "developer tools"],
        "screenshots": []
    }
    return JSONResponse(content=manifest_data)


# Service Worker
@app.get("/sw.js")
async def service_worker():
    """Serve the service worker script."""
    sw_js = """
const CACHE_NAME = 'swarmz-v1';
const CACHE_ASSETS = [
    '/',
    '/manifest.webmanifest',
    '/icon.svg',
    '/apple-touch-icon.svg'
];

// Install event - cache shell assets
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching shell assets');
                return cache.addAll(CACHE_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - network-first for API, cache-first for assets
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Network-first strategy for API endpoints and docs
    if (url.pathname.startsWith('/v1/') || url.pathname.startsWith('/docs/')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Clone the response for caching
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return response;
                })
                .catch(() => {
                    // Fall back to cache if network fails
                    return caches.match(request);
                })
        );
        return;
    }

    // Cache-first strategy for shell assets
    event.respondWith(
        caches.match(request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request).then(response => {
                    // Cache new assets
                    if (request.method === 'GET') {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                });
            })
    );
});
"""
    return HTMLResponse(content=sw_js, media_type="application/javascript")


# SVG Icons
@app.get("/icon.svg")
async def icon_svg():
    """Serve the app icon."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" rx="40" fill="url(#grad)"/>
  <text x="100" y="130" font-family="Arial, sans-serif" font-size="100" font-weight="bold" 
        text-anchor="middle" fill="#ffffff">⚡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


@app.get("/apple-touch-icon.svg")
async def apple_touch_icon():
    """Serve the Apple touch icon."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="180" height="180" fill="url(#grad)"/>
  <text x="90" y="120" font-family="Arial, sans-serif" font-size="90" font-weight="bold" 
        text-anchor="middle" fill="#ffffff">⚡</text>
</svg>"""
    return HTMLResponse(content=svg, media_type="image/svg+xml")


# REST API Endpoints
@app.get("/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SWARMZ API",
        "version": "1.0.0"
    }


@app.get("/v1/tasks")
async def list_tasks():
    """List all available tasks."""
    try:
        capabilities = swarmz.list_capabilities()
        return {
            "success": True,
            "tasks": capabilities,
            "count": len(capabilities)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/execute", response_model=TaskExecuteResponse)
async def execute_task(request: TaskExecuteRequest):
    """Execute a task with provided parameters."""
    try:
        result = swarmz.execute(request.task, **request.params)
        return TaskExecuteResponse(
            success=True,
            result=result
        )
    except ValueError as e:
        return TaskExecuteResponse(
            success=False,
            error=f"Task not found: {str(e)}"
        )
    except Exception as e:
        return TaskExecuteResponse(
            success=False,
            error=str(e)
        )


@app.get("/v1/audit")
async def get_audit_log():
    """Get the audit log of all operations."""
    try:
        audit = swarmz.get_audit_log()
        return {
            "success": True,
            "audit_log": audit,
            "count": len(audit)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/system/info")
async def system_info():
    """Get system information."""
    try:
        info = swarmz.execute("system_info")
        return {
            "success": True,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Main entry point for the web server."""
    import uvicorn
    
    # Get host and port
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    
    # Get LAN IP
    lan_ip = get_lan_ip()
    
    # Print startup information
    print("=" * 70)
    print("⚡ SWARMZ Web Server Starting...")
    print("=" * 70)
    print(f"\n📡 Server URLs:")
    print(f"   Local:    http://localhost:{port}")
    print(f"   LAN:      http://{lan_ip}:{port}")
    print(f"\n📚 API Documentation:")
    print(f"   OpenAPI:  http://localhost:{port}/docs")
    print(f"   OpenAPI:  http://{lan_ip}:{port}/docs")
    print(f"\n💡 Access SWARMZ from any device on your network using the LAN URL")
    print(f"📱 Add to Home Screen on mobile for PWA experience")
    print("=" * 70)
    print()
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
