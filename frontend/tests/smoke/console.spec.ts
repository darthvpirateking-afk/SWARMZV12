/**
 * SWARMZ Browser Smoke Tests — Console Surfaces
 *
 * Validates both main operator-console routes without requiring a live backend.
 * API calls will fail gracefully (network errors) so tests focus on:
 *  1. Page load and static shell render
 *  2. Key interactive elements are present and keyboard/click accessible
 *  3. User-initiated click flows produce expected UI state changes
 *
 * Console Surface A — Command Console  (chat + dispatch)
 * Console Surface B — Status Console   (system-status cards + refresh flows)
 */

import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function loadApp(page: Page): Promise<void> {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  // Wait for the main heading to confirm the React app has hydrated.
  await page.getByRole("heading", { name: /SWARMZ Frontend Chat/i }).waitFor();
}

/**
 * Returns the submit button inside the main chat form.
 * Scoped to `form` to avoid colliding with the "Send" button in CompanionCoreCard.
 */
function chatSendButton(page: Page) {
  return page.locator("form").getByRole("button", { name: /send/i });
}

// ---------------------------------------------------------------------------
// Console Surface A — Command Console
// ---------------------------------------------------------------------------

test.describe("Console Surface A — Command Console", () => {
  test("page loads and displays SWARMZ heading", async ({ page }) => {
    await loadApp(page);
    const heading = page.getByRole("heading", {
      name: /SWARMZ Frontend Chat/i,
    });
    await expect(heading).toBeVisible();
  });

  test("companion endpoint label is visible", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByText(/companion endpoint/i, { exact: false }),
    ).toBeVisible();
  });

  test("initial assistant greeting is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByText(/SWARMZ chat ready/i, { exact: false }),
    ).toBeVisible();
  });

  test("message textarea is present and focusable", async ({ page }) => {
    await loadApp(page);
    const textarea = page.getByPlaceholder(/type a message/i);
    await expect(textarea).toBeVisible();
    await textarea.focus();
    await expect(textarea).toBeFocused();
  });

  test("Send button is present and disabled when input is empty", async ({
    page,
  }) => {
    await loadApp(page);
    const send = chatSendButton(page);
    await expect(send).toBeVisible();
    await expect(send).toBeDisabled();
  });

  test("typing a message enables the Send button", async ({ page }) => {
    await loadApp(page);
    const textarea = page.getByPlaceholder(/type a message/i);
    const send = chatSendButton(page);

    await textarea.fill("Hello SWARMZ");
    await expect(send).toBeEnabled();
  });

  test("clearing message text disables the Send button again", async ({
    page,
  }) => {
    await loadApp(page);
    const textarea = page.getByPlaceholder(/type a message/i);
    const send = chatSendButton(page);

    await textarea.fill("temp");
    await expect(send).toBeEnabled();
    await textarea.fill("");
    await expect(send).toBeDisabled();
  });

  test("submitting a message appends the user message to the log", async ({
    page,
  }) => {
    await loadApp(page);
    const textarea = page.getByPlaceholder(/type a message/i);
    const send = chatSendButton(page);

    await textarea.fill("Smoke test dispatch");
    await send.click();

    // User message should appear immediately regardless of API outcome.
    await expect(
      page.getByText("Smoke test dispatch", { exact: false }),
    ).toBeVisible();
    // Textarea clears on submit.
    await expect(textarea).toHaveValue("");
  });

  test("submitting a message clears the textarea for the next input", async ({
    page,
  }) => {
    await loadApp(page);
    const textarea = page.getByPlaceholder(/type a message/i);
    const send = chatSendButton(page);

    await textarea.fill("keyboard flow check");
    await send.click();
    await expect(
      page.getByText("keyboard flow check", { exact: false }),
    ).toBeVisible();
    await expect(textarea).toHaveValue("");
  });
});

// ---------------------------------------------------------------------------
// Console Surface B — Status Console
// ---------------------------------------------------------------------------

test.describe("Console Surface B — Status Console", () => {
  test("Project Bootstrap card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /project bootstrap/i }),
    ).toBeVisible();
  });

  test("Bootstrap Refresh button is present and clickable", async ({
    page,
  }) => {
    await loadApp(page);
    // The Bootstrap card's <header> contains both the title and the Refresh button.
    const bootstrapHeader = page
      .locator("header")
      .filter({ hasText: /Project Bootstrap/ });
    const refreshBtn = bootstrapHeader.getByRole("button", {
      name: /refresh/i,
    });
    await expect(refreshBtn).toBeVisible();
    // Clicking must not throw; the button triggers an async status fetch.
    await refreshBtn.click();
    // After click the button should either show "Refreshing..." or return
    // to "Refresh" once the (failing) fetch resolves.  Either way it stays visible.
    await expect(refreshBtn).toBeVisible();
  });

  test("API Foundation card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /api foundation/i }),
    ).toBeVisible();
  });

  test("Database Layer card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /database layer/i }),
    ).toBeVisible();
  });

  test("Operator Auth card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /operator auth/i }),
    ).toBeVisible();
  });

  test("Companion Core card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /companion core/i }),
    ).toBeVisible();
  });

  test("Build Milestones card is rendered", async ({ page }) => {
    await loadApp(page);
    await expect(
      page.getByRole("heading", { name: /build milestones/i }),
    ).toBeVisible();
  });

  test("all status Refresh buttons are interactive", async ({ page }) => {
    await loadApp(page);
    const refreshBtns = page.getByRole("button", { name: /refresh/i });
    const count = await refreshBtns.count();
    expect(count).toBeGreaterThanOrEqual(1);
    // Each Refresh button must be accessible.
    for (let i = 0; i < count; i++) {
      await expect(refreshBtns.nth(i)).toBeVisible();
    }
  });

  test("page title is correct", async ({ page }) => {
    await loadApp(page);
    await expect(page).toHaveTitle(/swarmz/i);
  });
});
