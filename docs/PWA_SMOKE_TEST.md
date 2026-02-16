# SWARMZ PWA Smoke Test (LAN)

1) Start runtime (prints LAN + pairing URL + PIN source):
   ```powershell
   .\SWARMZ_UP.ps1
   ```
   Or directly: `python run_swarmz.py`.

2) From your phone on the same Wi‑Fi, open the LAN URL printed (http://<lan>:8012). Install the PWA if prompted.

3) Pair:
   - Base URL defaults to the current page.
   - Enter Operator PIN (env `SWARMZ_OPERATOR_PIN`, `data/config.json`, or generated in `data/operator_pin.txt`).
   - Tap Pair. Token is stored locally.

4) Verify endpoints (optional from desktop):
   ```powershell
   curl http://127.0.0.1:8012/openapi.json | findstr /i pairing
   curl -X POST http://127.0.0.1:8012/v1/pairing/pair -H "Content-Type: application/json" -d "{\"pin\":\"<PIN>\"}"
   ```

5) Dispatch and view runs from the PWA:
   - Tap Dispatch and enter a goal.
   - Runs list updates; select to view details.
   - Audit panel shows latest events (tail of `data/audit.jsonl`).

6) Galileo check (optional):
   ```powershell
   curl http://127.0.0.1:8012/openapi.json | findstr /i galileo
   curl -X POST "http://127.0.0.1:8012/v1/galileo/run" -H "Content-Type: application/json" -d "{\"domain\":\"routing_optimization\",\"seed\":12345,\"n_hypotheses\":5}"
   ```

Data stays under `./data` and `./packs`. No cloud dependencies.
