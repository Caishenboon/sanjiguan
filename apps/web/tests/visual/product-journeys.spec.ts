import { expect, test, type Page } from "@playwright/test";

const profileId = "019f9f61-5dc9-79cf-8b92-000000000001";
const divinationId = "019f9f61-5dc9-79cf-8b92-000000000002";

async function seedSubject(page: Page) {
  await page.goto("/");
  await page.evaluate(({ id }) => {
    sessionStorage.setItem("sanjiguan:product-session:v1", JSON.stringify({
      subject: { id, name: "虚构测试主体", birthDate: "1990-01-01", timePrecision: "unknown" },
      chronicles: [],
    }));
  }, { id: profileId });
}

test("journey A: first use creates a subject without inventing an unknown birth time", async ({ page }) => {
  let requestBody: Record<string, any> = {};
  await page.route("**/api/v1/profiles", async (route) => {
    requestBody = route.request().postDataJSON();
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: profileId }) });
  });
  await page.goto("/");
  await expect(page.locator("nav[aria-label='普通用户主导航'] a")).toHaveCount(5);
  await page.getByRole("link", { name: "建立我的资料" }).click();
  await page.getByLabel("如何称呼这个主体").fill("虚构测试主体");
  await page.getByLabel("出生日期").fill("1990-01-01");
  await page.getByLabel("出生时刻未知").check();
  await page.getByLabel("出生地点原文").fill("虚构城市");
  await page.getByLabel("我确认以上是原始输入").check();
  await page.getByRole("button", { name: "保存资料" }).click();
  await expect(page.getByRole("heading", { name: "欢迎回来，虚构测试主体" })).toBeVisible();
  expect(requestBody.birth.local_time).toBeNull();
  expect(requestBody.birth.time_precision).toBe("unknown");
});

test("journey B: save a record and find it in 三际录", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/journal`, async (route) => {
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "record-journey-b" }) });
  });
  await page.goto("/records");
  await page.getByRole("article").filter({ hasText: "人生事件" }).getByRole("link", { name: "开始记录" }).click();
  await page.getByLabel("简短标题").fill("虚构的学习里程碑");
  await page.getByLabel("当时发生了什么").fill("这是一条完全虚构的产品旅程测试记录。");
  await page.getByRole("button", { name: "保存到三际录" }).click();
  await expect(page).toHaveURL(/\/chronicle/);
  await expect(page.getByText("虚构的学习里程碑")).toBeVisible();
  await page.getByRole("link", { name: /虚构的学习里程碑/ }).click();
  await expect(page.getByRole("heading", { name: "当时记录了什么" })).toBeVisible();
});

test("journey C: execute physical three-coin and read progressive result details", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/divinations/three-coin`, async (route) => {
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({
      id: divinationId,
      research_status: "research_active",
      notice: "仅记录实物三钱结果；未生成卦义、评分或命理结论。",
      result_hash: "sha256:fixture-only-product-journey",
      engine_result: {
        lines: [
          { line_position: 1, sum: 8, line_state: "young_yin", moving: false },
          { line_position: 2, sum: 7, line_state: "young_yang", moving: false },
          { line_position: 3, sum: 9, line_state: "old_yang", moving: true },
          { line_position: 4, sum: 8, line_state: "young_yin", moving: false },
          { line_position: 5, sum: 7, line_state: "young_yang", moving: false },
          { line_position: 6, sum: 6, line_state: "old_yin", moving: true },
        ],
        moving_lines: [3, 6],
        base_hexagram: { sequence: 63, name: "既济", key: "ji_ji" },
        transformed_hexagram: { sequence: 37, name: "家人", key: "jia_ren" },
        method_version: "1.0.0",
        mapping_asset: { asset_version: "1.0.0" },
      },
    }) });
  });
  await page.goto("/consult");
  await page.getByRole("article").filter({ hasText: "易经三钱" }).getByRole("link", { name: "开始" }).click();
  await page.getByLabel("这次正式占问什么").fill("虚构问题：接下来如何安排学习？");
  await page.getByLabel("我确认这是一次正式实物投掷").check();
  await page.getByRole("button", { name: "形成机械结构" }).click();
  await expect(page.getByRole("heading", { name: "易经三钱机械结果" })).toBeVisible();
  await expect(page.getByText("既济 → 家人")).toBeVisible();
  await expect(page.getByText("这不是吉凶、应期或人生结论。")).toBeVisible();
  await page.getByText("研究详情", { exact: true }).click();
  await expect(page.getByText("sha256:fixture-only-product-journey")).toBeVisible();
});

test("journey D: liuxiang explains why it cannot conclude without exposing synthetic candidates", async ({ page }) => {
  await seedSubject(page);
  await page.goto("/consult/liuxiang");
  await expect(page.getByRole("heading", { name: "资料不足，暂不成断" })).toBeVisible();
  await expect(page.getByText("真实映射规则尚未通过审校")).toBeVisible();
  await expect(page.getByText("synthetic_conformance")).toHaveCount(0);
  await expect(page.getByText(/聚合哈希|a08cb815|81a43d8/)).toHaveCount(0);
});

test("ordinary session cannot enter research administration", async ({ page }) => {
  await page.goto("/admin/research");
  await expect(page).toHaveURL(/\/forbidden$/);
  await expect(page.getByRole("heading", { name: "研究后台只对授权角色开放" })).toBeVisible();
});

test("network failure is explained and can be retried", async ({ page }) => {
  await seedSubject(page);
  let attempts = 0;
  await page.route(`**/api/v1/profiles/${profileId}/journal`, async (route) => {
    attempts += 1;
    if (attempts === 1) await route.abort("failed");
    else await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "retry-record" }) });
  });
  await page.goto("/records/new?type=reflection");
  await page.getByLabel("简短标题").fill("虚构重试记录");
  await page.getByLabel("当时发生了什么").fill("第一次网络失败，第二次保存成功。");
  await page.getByRole("button", { name: "保存到三际录" }).click();
  await expect(page.getByRole("heading", { name: "网络失败，可以重试" })).toBeVisible();
  await page.getByRole("button", { name: "保存到三际录" }).click();
  await expect(page.getByText("虚构重试记录")).toBeVisible();
});

test("legacy profile routes redirect to the product spine", async ({ page }) => {
  await page.goto("/profile/demo/journal");
  await expect(page).toHaveURL(/\/records\?subject=demo$/);
  await page.goto("/profile/demo/analysis");
  await expect(page).toHaveURL(/\/consult\/liuxiang\?subject=demo$/);
});
