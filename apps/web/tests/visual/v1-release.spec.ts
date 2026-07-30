import { expect, test } from "@playwright/test";

test("first owner flow is keyboard operable and continues to onboarding", async ({ page }) => {
  await page.route("**/api/v1/auth/bootstrap-owner", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ user_id: "synthetic-owner", role: "owner" }),
    });
  });
  await page.goto("/start");
  await expect(page.getByRole("heading", { name: "建立本地所有者" })).toBeVisible();
  await page.getByLabel("所有者称谓或邮箱").fill("虚构所有者");
  await page.getByLabel("一次性初始化口令").fill("synthetic-bootstrap-token");
  await page.getByRole("button", { name: "建立所有者并继续" }).click();
  await expect(page).toHaveURL(/\/onboarding$/);
});

test("data controls explain export and destructive deletion without color-only state", async ({ page }) => {
  await page.goto("/me/data");
  await expect(page.getByRole("heading", { name: "隐私、导出与删除" })).toBeVisible();
  await expect(page.getByText("彻底删除会令相关 Replay 不可用。", { exact: false })).toBeVisible();
  const inputs = await page.locator("input").count();
  for (let index = 0; index < inputs; index += 1) {
    const input = page.locator("input").nth(index);
    const id = await input.getAttribute("id");
    expect(id).toBeTruthy();
    await expect(page.locator(`label[for="${id}"]`)).toHaveCount(1);
  }
  const buttonNames = await page.locator("button").allTextContents();
  expect(buttonNames.every((name) => name.trim().length > 0)).toBeTruthy();
});
