import { expect, test } from "@playwright/test";

const deterministicFonts = [
  { descriptor: '16px "Noto Sans SC"', sample: "三际观" },
  { descriptor: '16px "Noto Serif SC"', sample: "三际观" },
  { descriptor: '16px "Noto Sans Mono"', sample: "sha256abcdef0123456789" },
] as const;

async function requireDeterministicFonts(page: import("@playwright/test").Page) {
  const availability = await page.evaluate(async (fonts) => {
    await Promise.all(fonts.map(({ descriptor, sample }) => document.fonts.load(descriptor, sample)));
    await document.fonts.ready;
    return Object.fromEntries(
      fonts.map(({ descriptor, sample }) => [
        descriptor,
        document.fonts.check(descriptor, sample),
      ]),
    );
  }, deterministicFonts);
  expect(availability).toEqual(
    Object.fromEntries(deterministicFonts.map(({ descriptor }) => [descriptor, true])),
  );
}

const pages = [
  ["home", "/"],
  ["research", "/admin/research"],
  ["three-coin", "/admin/research/three-coin"],
  ["bazi", "/admin/research/bazi-methods"],
  ["ziwei", "/admin/research/ziwei"],
  ["oracles", "/admin/research/oracles"],
] as const;

for (const [name, path] of pages) {
  test(`${name} fixed visual`, async ({ page }) => {
    if (path.startsWith("/admin/")) {
      await page.setExtraHTTPHeaders({ "x-sanji-test-role": "research_admin" });
    }
    await page.goto(path);
    await expect(page.locator("main")).toBeVisible();
    await requireDeterministicFonts(page);
    await expect(page).toHaveScreenshot(`${name}.png`, {
      fullPage: false,
      animations: "disabled",
    });
  });
}

test("research warning state remains readable", async ({ page }) => {
  await page.setExtraHTTPHeaders({ "x-sanji-test-role": "research_admin" });
  await page.goto("/admin/research");
  await requireDeterministicFonts(page);
  await expect(page.locator("main")).toBeVisible();
  await expect(page).toHaveScreenshot("research-warning.png", {
    fullPage: false,
    animations: "disabled",
  });
});
