import { rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

// E2E: backend (FastAPI) build qilingan frontendni o'zi xizmat qiladi; har ishga tushishda toza baza.
// Ishga tushirish:  npm run e2e  (= npm run build && npx playwright test; birinchi marta: npx playwright install chromium)
// Chromium boshqa joyda bo'lsa: PW_CHROMIUM=/path/to/chrome npx playwright test
const PORT = Number(process.env.E2E_PORT ?? 8765);
const PYTHON = process.env.MEBELIX_PYTHON ?? (process.platform === "win32" ? "python" : "python3");
// har ishga tushishda toza e2e bazasi (faqat asosiy jarayonda — test ishchilari konfiguratsiyani qayta o'qiydi)
if (!process.env.TEST_WORKER_INDEX) {
  try {
    rmSync(fileURLToPath(new URL("../backend/e2e_test.db", import.meta.url)), { force: true });
  } catch { /* band bo'lsa — eski baza bilan davom etadi */ }
}

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
    // Windows, Linux va macOS'da bir xil: toza baza, backend papkasida uvicorn (Python — MEBELIX_PYTHON yoki python/python3)
    command: `${PYTHON} -m uvicorn app.main:app --port ${PORT}`,
    cwd: fileURLToPath(new URL("../backend", import.meta.url)),
    env: { MEBELIX_DB_URL: "sqlite:///./e2e_test.db" },
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
