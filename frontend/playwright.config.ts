import { defineConfig } from "@playwright/test";

// E2E: backend (FastAPI) build qilingan frontendni o'zi xizmat qiladi; har ishga tushishda toza baza.
// Ishga tushirish:  npm run build && npx playwright test
// Chromium boshqa joyda bo'lsa: PW_CHROMIUM=/path/to/chrome npx playwright test
const PORT = Number(process.env.E2E_PORT ?? 8765);

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    viewport: { width: 1440, height: 900 },
    launchOptions: process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {},
    trace: "retain-on-failure",
  },
  webServer: {
    command: `cd ../backend && rm -f e2e_test.db && MEBELIX_DB_URL=sqlite:///./e2e_test.db python3 -m uvicorn app.main:app --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
