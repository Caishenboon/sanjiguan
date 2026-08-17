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
  await expect(page.getByText("彻底删除可能令历史复演不可用。", { exact: false })).toBeVisible();
  const inputs = await page.locator("input").count();
  for (let index = 0; index < inputs; index += 1) {
    const input = page.locator("input").nth(index);
    const id = await input.getAttribute("id");
    expect(id).toBeTruthy();
    await expect(page.locator(`label[for="${id}"]`)).toHaveCount(1);
  }
  const buttonNames = await page.locator("button").allTextContents();
  expect(buttonNames.every((name) => name.trim().length > 0)).toBeTruthy();
  await page.getByRole("button", { name: "删除账号及私人数据" }).click();
  const dialog=page.getByRole("dialog", { name: "确认彻底删除？" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("相关历史可能无法复演")).toBeVisible();
  const cancel=dialog.getByRole("button", { name: "返回检查" });
  const confirm=dialog.getByRole("button", { name: "确认彻底删除" });
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(confirm).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole("button", { name: "删除账号及私人数据" })).toBeFocused();
});

test("onboarding draft can resume without inventing missing birth time", async ({ page }) => {
  await page.goto("/onboarding");
  await page.getByLabel("如何称呼这个主体").fill("虚构续卷主体");
  await page.getByLabel("出生时刻未知").check();
  await page.getByRole("link", { name: "暂存退出" }).click();
  await page.reload();
  await expect(page.getByLabel("如何称呼这个主体")).toHaveValue("虚构续卷主体");
  await expect(page.getByLabel("出生时刻未知")).toBeChecked();
  await expect(page.getByText("第 1—3 步，共 8 步")).toBeVisible();
});
