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
    await page.goto(path);
    await expect(page.locator("main")).toBeVisible();
    await requireDeterministicFonts(page);
    await expect(page).toHaveScreenshot(`${name}.png`, {
      fullPage: false,
      animations: "disabled",
    });
  });
}

test("empty error and disabled states remain readable", async ({ page }) => {
  await page.goto("/admin/research");
  await requireDeterministicFonts(page);
  await page.evaluate(() => {
    const main = document.querySelector("main");
    if (main) main.innerHTML = `
      <section class="sanji-grid">
        <div class="sanji-empty"><h3>尚无记录</h3><p>等待虚构研究输入。</p></div>
        <div class="sanji-empty sanji-error" role="alert"><h3>无法载入</h3><p>MODULE_DISABLED</p></div>
        <aside class="sanji-warning">研究禁用状态 · 不会返回占位计算</aside>
      </section>`;
  });
  await expect(page).toHaveScreenshot("states-empty-error-disabled.png", {
    fullPage: false,
    animations: "disabled",
  });
});
