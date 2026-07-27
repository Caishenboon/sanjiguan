import { defineConfig, devices } from "@playwright/test";

const localChannel = process.env.CI ? undefined : "chrome";

export default defineConfig({
  testDir: "./tests/visual",
  snapshotPathTemplate: "{testDir}/__screenshots__/{projectName}/{arg}{ext}",
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.012 } },
  use: { baseURL: "http://127.0.0.1:3000", locale: "zh-CN" },
  webServer: {
    command: "pnpm start",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  projects: [
    { name: "chromium-desktop-dark", use: { ...devices["Desktop Chrome"], channel: localChannel, colorScheme: "dark", viewport: { width: 1440, height: 1100 } } },
    { name: "chromium-tablet-light", use: { ...devices["iPad (gen 7)"], browserName: "chromium", channel: localChannel, colorScheme: "light" } },
    { name: "chromium-mobile-dark", use: { ...devices["iPhone 13"], browserName: "chromium", channel: localChannel, colorScheme: "dark" } },
  ],
});
