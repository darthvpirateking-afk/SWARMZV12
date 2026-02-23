import { defineConfig, devices } from "@playwright/test";

/**
 * SWARMZ Browser Smoke Configuration
 *
 * Runs against the Vite preview build (`npm run build && npm run preview`).
 * Two project slices map to the two main operator-console surfaces:
 *   • console-main  – the primary operator chat / command surface
 *   • console-status – the system-status / monitoring surface
 *
 * In CI the server is started automatically via `webServer`.
 * Locally, if a preview server is already running on port 4173 it will be reused.
 */

const PREVIEW_PORT = 4173;
const PREVIEW_URL = `http://localhost:${PREVIEW_PORT}`;

export default defineConfig({
  testDir: "./tests/smoke",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],

  use: {
    baseURL: PREVIEW_URL,
    /* Capture traces on first retry so CI artifacts are actionable. */
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  webServer: {
    command: `npm run preview -- --port ${PREVIEW_PORT}`,
    url: PREVIEW_URL,
    reuseExistingServer: !process.env.CI,
    stdout: "ignore",
    stderr: "pipe",
  },

  projects: [
    {
      name: "console-main",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "console-status",
      use: { ...devices["Desktop Firefox"] },
    },
  ],
});
