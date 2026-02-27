import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse


def create_hologram_api(reconciler, publisher, auth_check=None):
    app = FastAPI()
    ws_clients: set = set()

    @app.get("/snapshot/latest")
    async def latest_snapshot():
        snap = reconciler.get_latest_snapshot()
        return JSONResponse(content=snap)

    @app.post("/patch")
    async def patch_hologram(req: Request):
        body = await req.json()
        if auth_check and not auth_check(req):
            raise HTTPException(status_code=403, detail="forbidden")
        if "op" not in body or "target" not in body:
            raise HTTPException(status_code=400, detail="invalid patch")
        publisher.publish_diff({"tick": reconciler.state["meta"]["tick"] + 1, "patch": body})
        return {"status": "ok", "applied": body}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        ws_clients.add(ws)

        # Capture the running event loop so the synchronous publisher callback
        # can schedule coroutines from the reconciler background thread.
        loop = asyncio.get_event_loop()

        snap = reconciler.get_latest_snapshot()
        await ws.send_text(json.dumps({"type": "hologram.snapshot", "snapshot": snap}))

        def push(event):
            """Called synchronously from HologramPublisher (background thread)."""
            try:
                asyncio.run_coroutine_threadsafe(
                    ws.send_text(json.dumps(event)), loop
                )
            except Exception:
                pass

        publisher.subscribe(push)

        try:
            while True:
                await ws.receive_text()  # keep connection alive; handle client pings
        except WebSocketDisconnect:
            ws_clients.discard(ws)

    return app
