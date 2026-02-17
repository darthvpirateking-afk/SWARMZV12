# Phone Setup (SWARMZ)

## Start the server
- Open PowerShell in repo root
- Run: `./SWARMZ_UP.ps1`
- Ensure `OPERATOR_KEY` is set in the environment if you require operator-gated actions

## Connect from your phone
- Make sure the phone is on the same Wi‑Fi/LAN as the PC
- Open the LAN URL printed by the launcher, e.g. `http://192.168.x.x:8012/`
- If prompted, enter the Operator PIN/Key (matches `OPERATOR_KEY` on the server)

## Windows Firewall (documented; do not auto-run)
```
netsh advfirewall firewall add rule name="SWARMZ 8012 TCP" dir=in action=allow protocol=TCP localport=8012
```

## Notes
- Guest/isolated Wi‑Fi networks may block LAN access; use a trusted LAN.
- If port 8012 is busy, set `KILL_PORT=1` before launching to auto-stop the listener.
- Use the "Reset Cache" button in the UI if the PWA gets stale on the phone.
