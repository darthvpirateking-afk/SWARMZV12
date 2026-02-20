# SWARMZ Companion Frontend (React + Vite)

This frontend is a React + Vite TypeScript chat client for the SWARMZ companion endpoint.

## Endpoint

- POST `/v1/companion/message`
- Base URL comes from `VITE_API_BASE_URL`
- Request body: `{ "text": "hello" }`

## Folder structure

```text
ui/
  index.html
  package.json
  tsconfig.json
  vite.config.ts
  .env.example
  src/
    main.tsx
    App.tsx
    styles.css
    lib/
      api.ts
    hooks/
      useChat.ts
    types/
      chat.ts
    components/
      Composer.tsx
      MessageList.tsx
```

## Setup

```bash
cd ui
npm install
```

## Run (development)

```bash
npm run dev
```

Open the URL shown by Vite (default `http://localhost:5173`).

## Build

```bash
npm run build
```

## Preview production build

```bash
npm run preview
```

## Environment variables

Copy `.env.example` to `.env` and edit as needed.

- `VITE_API_BASE_URL`: required API origin to call.
- `VITE_OPERATOR_KEY`: optional operator PIN/header value; sent as `x-operator-key` only when provided.

## Working fetch() call

Implemented in `src/lib/api.ts`:

```ts
await fetch(`${baseUrl}/v1/companion/message`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    ...(operatorKey ? { "x-operator-key": operatorKey } : {}),
  },
  body: JSON.stringify({ text }),
});
```
