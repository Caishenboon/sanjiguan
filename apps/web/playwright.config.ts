import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  snapshotPathTemplate: "{testDir}/__screenshots__/{platform}/{projectName}/{arg}{ext}",
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.012 } },
  use: {
    baseURL: "http://127.0.0.1:3000",
    locale: "zh-CN",
    timezoneId: "UTC",
  },
  webServer: {
    command: "pnpm start",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  projects: [
    {
      name: "chromium-desktop-dark",
      use: {
        browserName: "chromium",
        colorScheme: "dark",
        viewport: { width: 1440, height: 1100 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: "chromium-tablet-light",
      use: {
        browserName: "chromium",
        colorScheme: "light",
        viewport: { width: 810, height: 1080 },
        deviceScaleFactor: 1,
      },
    },
    {
      name: "chromium-mobile-dark",
      use: {
        browserName: "chromium",
        colorScheme: "dark",
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 1,
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
});
