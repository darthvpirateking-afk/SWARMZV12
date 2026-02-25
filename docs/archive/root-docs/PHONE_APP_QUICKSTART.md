# NEXUSMON Phone + App Quickstart (No Tech Steps)

## 1-Button Start (PC)
- Double-click: `NEXUSMON_ONE_BUTTON_START.cmd`
- It auto-sets local profile, clears blocked port, starts NEXUSMON, and opens browser.

## Use on Phone (same Wi-Fi)
1. Keep NEXUSMON running on your PC.
2. On phone browser, open the LAN URL shown in the PC terminal:
   - `http://<LAN_IP>:8012/`
3. Pair using PIN from:
   - `data/operator_pin.txt`

## Make it an "App" on Phone
Yes — NEXUSMON can be installed as a PWA app (home-screen app).

- Open NEXUSMON URL on phone browser
- Tap browser menu
- Tap **Install app** / **Add to Home Screen**

That creates an app-like icon and full-screen launcher.

## Publish to Play Store / App Store (native wrapper)

Yes — now set up in this repo:
- Wrapper folder: `mobile/app_store_wrapper/`
- One-command Android setup: `APP_STORE_BUILD.cmd`

Manual commands (from `mobile/app_store_wrapper`):
- `npm install`
- `npm run android:add`
- `npm run cap:sync`
- `npm run android:open`

Then build signed bundle in Android Studio for Play Store upload.

## If Phone Can't Connect
- Confirm phone and PC are on the same Wi-Fi
- Re-open one-button starter
- Use local check on PC: `http://127.0.0.1:8012/v1/health`
- If needed, run: `python tools/nexusmon_doctor.py`

