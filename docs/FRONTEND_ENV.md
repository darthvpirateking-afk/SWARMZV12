# Frontend API Environment Contract

## Canonical Variable
- `VITE_API_BASE_URL`

## Backward-Compatible Fallback
- `VITE_API_URL` (supported during migration)

## Resolution Order
1. `VITE_API_BASE_URL`
2. `VITE_API_URL`
3. Surface-specific default:
   - `frontend`: existing production default
   - `ui`: `http://localhost:8000` for local dev
   - generic utility calls may use `window.location.origin`

## Notes
- Keep trailing slash normalization in clients.
- Do not hardcode endpoint hosts in component logic.
