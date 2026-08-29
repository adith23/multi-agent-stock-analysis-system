import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const API_PATTERN = "http://localhost:8000/api/v1/**";
const RUN_ID = "11111111-1111-4111-8111-111111111111";

type BackendRole = "portfolio_manager" | "risk_officer" | "research_analyst";

function userForRole(role: BackendRole) {
  return {
    id: "user-1",
    username: "institutional.test",
    email: "user@example.com",
    first_name: "Institutional",
    last_name: "User",
    job_title: "Investment Professional",
    role,
  };
}

function analysisRun(symbol: string) {
  return {
    id: RUN_ID,
    created_at: "2026-08-27T00:00:00Z",
    updated_at: "2026-08-27T00:00:00Z",
    symbol,
    exchange: "NASDAQ",
    scope: "single",
    status: "pending",
    current_stage: "",
    initiated_by: "user-1",
    celery_task_id: "",
    data_cutoff_at: "2026-08-27T00:00:00Z",
    configuration_hash: "hash",
    manifest_hash: "",
    error_message: "",
    started_at: null,
    completed_at: null,
    steps: [],
  };
}

async function mockBackend(page: Page, getRole: () => BackendRole = () => "research_analyst") {
  await page.route(API_PATTERN, async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path.endsWith("/auth/token/") && request.method() === "POST") {
      return route.fulfill({ json: { access: "e2e-access", refresh: "e2e-refresh" } });
    }
    if (path.endsWith("/auth/me/")) return route.fulfill({ json: userForRole(getRole()) });
    if (path.endsWith("/analysis/") && request.method() === "POST") {
      const body = request.postDataJSON() as { symbol: string };
      return route.fulfill({ status: 201, json: analysisRun(body.symbol) });
    }
    if (path.includes("/stream/")) return route.fulfill({ status: 503, json: { detail: "Stream unavailable in E2E fixture." } });
    return route.fulfill({ status: 404, json: { detail: "Fixture endpoint not configured." } });
  });
}

async function seedSession(page: Page) {
  await page.context().addCookies([{ name: "conclave_session", value: "1", domain: "127.0.0.1", path: "/" }]);
  await page.addInitScript(() => {
    window.localStorage.setItem("conclave_access_token", "e2e-access");
    window.localStorage.setItem("conclave_refresh_token", "e2e-refresh");
  });
}

test("authenticates through the backend identity contract", async ({ page }) => {
  await mockBackend(page, () => "portfolio_manager");
  await page.goto("/login");
  await page.getByLabel("Username").fill("institutional.test");
  await page.getByLabel("Password").fill("correct-horse-battery-staple");
  await page.getByRole("button", { name: "Enter terminal" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText("Portfolio Manager")).toBeVisible();
});

test("runs analysis and supports keyboard tab navigation", async ({ page }) => {
  await seedSession(page);
  await mockBackend(page);
  await page.goto("/");

  await page.keyboard.press("Control+K");
  const ticker = page.getByRole("textbox", { name: "Ticker symbol" });
  await expect(ticker).toBeFocused();
  await ticker.fill("aapl");
  const submitted = page.waitForRequest((request) => request.method() === "POST" && request.url().endsWith("/analysis/"));
  await ticker.press("Enter");
  await submitted;
  await expect(page.getByText("AAPL").first()).toBeVisible();

  await page.keyboard.press("4");
  await expect(page.getByRole("tab", { name: "Risk + Compliance" })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "Risk + Compliance" }).press("End");
  await expect(page.getByRole("tab", { name: "Audit" })).toBeFocused();
});

test("enforces backend roles and has no detectable WCAG violations @visual", async ({ page }) => {
  let role: BackendRole = "portfolio_manager";
  await seedSession(page);
  await mockBackend(page, () => role);
  await page.goto("/");
  await expect(page.getByLabel("Decision rationale")).toBeVisible();

  role = "risk_officer";
  await page.reload();
  await expect(page.getByLabel("Decision rationale")).toHaveCount(0);

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations).toEqual([]);
  await expect(page).toHaveScreenshot("terminal-risk-officer.png", { animations: "disabled", fullPage: true });
});

test("uses collapsible sidebar drawers at the compact desktop breakpoint", async ({ page }) => {
  await page.setViewportSize({ width: 1180, height: 800 });
  await seedSession(page);
  await mockBackend(page);
  await page.goto("/");

  const pipelineToggle = page.getByRole("button", { name: "Expand agent pipeline" });
  await expect(pipelineToggle).toHaveAttribute("aria-expanded", "false");
  await pipelineToggle.click();
  await expect(page.getByRole("complementary", { name: "Agent pipeline" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Expand agent pipeline" })).toHaveAttribute("aria-expanded", "false");
});
