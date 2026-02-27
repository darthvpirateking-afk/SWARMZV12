# Nexusmon Hologram Cockpit (local dev)

1. Install:
   ```
   npm install
   ```

2. Start dev server (proxies `/hologram` to backend at `http://localhost:8000`):
   ```
   npm run dev
   ```

3. Open:
   ```
   http://localhost:5173
   ```

4. Notes:
   - Ensure your backend (nexusmon server) is running on `http://localhost:8000` and exposes `/hologram/ws` and `/hologram/snapshot/latest`.
   - Adjust the proxy target in `vite.config.js` if your backend runs on a different port.
   - WebSocket proxy (`ws: true`) is enabled in `vite.config.js` so live diffs work in dev mode.
   - For production, build with `npm run build` and serve the `dist/` folder behind the same origin as the backend (or configure CORS).
