import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/evidence",
  workers: 1,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:3000",
    browserName: "chromium",
    colorScheme: "dark",
    locale: "zh-CN",
    timezoneId: "UTC",
    serviceWorkers: "block",
  },
  webServer: {
    command: "pnpm start",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: { ...process.env, SANJI_RESEARCH_UI_TEST_MODE: "1" },
  },
});
