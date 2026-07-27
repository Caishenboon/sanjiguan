import { expect, test } from "@playwright/test";

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
    await expect(page).toHaveScreenshot(`${name}.png`, {
      fullPage: false,
      animations: "disabled",
    });
  });
}

test("empty error and disabled states remain readable", async ({ page }) => {
  await page.goto("/admin/research");
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
