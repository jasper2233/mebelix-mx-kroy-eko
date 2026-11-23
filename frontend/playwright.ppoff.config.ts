import { rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";
import base from "./playwright.config";

// 2026-11-23: stanok postprotsessorlari MES tizimida — MX standart rejimi (MEBELIX_PP_ENABLED yo'q / 0) uchun alohida e2e.
// Ishga tushirish:  npm run build && npx playwright test -c playwright.ppoff.config.ts
const PORT = Number(process.env.E2E_PPOFF_PORT ?? 8766);
const PYTHON = process.env.MEBELIX_PYTHON ?? (process.platform === "win32" ? "python" : "python3");
if (!process.env.TEST_WORKER_INDEX) {
  try {
    rmSync(fileURLToPath(new URL("../backend/e2e_ppoff.db", import.meta.url)), { force: true });
  } catch { /* band bo'lsa — eski baza bilan */ }
}

export default defineConfig({
  ...base,
  testDir: "./e2e-ppoff",
  use: { ...base.use, baseURL: `http://127.0.0.1:${PORT}` },
  webServer: {
    command: `"${PYTHON}" -m uvicorn app.main:app --port ${PORT}`,
    cwd: fileURLToPath(new URL("../backend", import.meta.url)),
    env: { MEBELIX_DB_URL: "sqlite:///./e2e_ppoff.db", MEBELIX_PP_ENABLED: "0" },
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
