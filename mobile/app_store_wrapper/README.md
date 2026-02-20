# SWARMZ App Store Wrapper (Capacitor)

This is a native wrapper so SWARMZ can be submitted to Google Play and Apple App Store.

## What this does
- Creates Android/iOS native shells.
- Loads your live SWARMZ app from: `https://swarmzV10-.onrender.com`.

## Quick start

From this folder:

```bash
npm install
npm run android:add
npm run cap:sync
npm run android:open
```

For iOS (macOS only):

```bash
npm install
npm run ios:add
npm run cap:sync
npm run ios:open
```

## Build for stores

### Google Play
1. Open Android Studio via `npm run android:open`
2. Set app icon, package details, and signing config
3. Build signed AAB (`Build > Generate Signed Bundle / APK`)
4. Upload AAB to Play Console

### Apple App Store
1. Open Xcode via `npm run ios:open`
2. Configure signing + bundle ID (`com.swarmz.app` or your final ID)
3. Archive and upload through Xcode Organizer
4. Submit in App Store Connect

## Important notes
- This wrapper depends on your Render URL being online.
- For full offline native behavior, you would ship local web assets instead of remote URL.
- Before store submission, replace placeholder app metadata (name, icons, screenshots, privacy policy links).

## Store prep files (added)
- Play checklist: `store/PLAY_STORE_RELEASE_CHECKLIST.md`
- App Store checklist: `store/APP_STORE_CONNECT_RELEASE_CHECKLIST.md`
- Metadata template: `store/APP_METADATA_TEMPLATE.json`
- Submission notes: `store/STORE_SUBMISSION_NOTES.md`
- Privacy policy draft: `../../docs/PRIVACY_POLICY.md`
