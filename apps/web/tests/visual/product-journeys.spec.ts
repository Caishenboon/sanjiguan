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
  await page.getByLabel("经度").fill("121.473700");
  await page.getByLabel("纬度").fill("31.230400");
  await page.getByLabel("我确认以上是原始输入").check();
  await page.getByRole("button", { name: "保存资料" }).click();
  await expect(page.getByRole("heading", { name: "欢迎回来，虚构测试主体" })).toBeVisible();
  expect(requestBody.birth.local_time).toBeNull();
  expect(requestBody.birth.time_precision).toBe("unknown");
});

test("journey B: save a record and find it in 三际录", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/journal`, async (route) => {
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "record-journey-b", archive_id: "archive-journey-b" }) });
  });
  await page.route("**/api/v1/chronicle?*", async (route) => route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[{
    id:"archive-journey-b",profile_id:profileId,execution_id:null,entry_type:"record",title:"虚构的学习里程碑",status:"recorded",replay_available:false,created_at:"2026-07-29T00:00:00Z",withdrawn:false,
  }]})}));
  await page.route("**/api/v1/chronicle/archive-journey-b", async (route) => route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({
    id:"archive-journey-b",profile_id:profileId,execution_id:null,entry_type:"record",title:"虚构的学习里程碑",note:"",status:"recorded",candidate_summary:[],engine_version:null,ruleset_version:null,evidence_policy_version:null,output_hash:null,trace_hash:null,replay_available:false,research_notice:null,created_at:"2026-07-29T00:00:00Z",
  })}));
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
  const divinationPayload = {
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
    };
  await page.route(`**/api/v1/profiles/${profileId}/divinations/three-coin`, async (route) => {
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(divinationPayload) });
  });
  await page.route(`**/api/v1/divinations/${divinationId}`, async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(divinationPayload) });
  });
  await page.route("**/api/v1/traditional-complete/execute", async (route) => {
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "traditional-journey-c" }) });
  });
  await page.goto("/consult");
  await page.getByRole("article").filter({ hasText: "易经三钱" }).getByRole("link", { name: "开始" }).click();
  await page.getByLabel("这次正式占问什么").fill("虚构问题：接下来如何安排学习？");
  const tosses = [
    ["tails", "heads", "heads"],
    ["tails", "tails", "heads"],
    ["heads", "heads", "heads"],
    ["tails", "heads", "heads"],
    ["tails", "tails", "heads"],
    ["tails", "tails", "tails"],
  ];
  const lineNames = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"];
  for (const [lineIndex, row] of tosses.entries()) {
    for (const [coinIndex, face] of row.entries()) {
      await page.getByLabel(`${lineNames[lineIndex]}第${coinIndex + 1}枚`).selectOption(face);
    }
  }
  await page.getByLabel("我确认这是一次正式实物投掷").check();
  await page.getByRole("button", { name: "形成机械结构" }).click();
  await expect(page.getByRole("heading", { name: "易经三钱机械结果" })).toBeVisible();
  await expect(page.getByText("既济 → 家人")).toBeVisible();
  await expect(page.getByText("这不是吉凶、应期或人生结论。")).toBeVisible();
  await page.getByText("研究详情", { exact: true }).click();
  await expect(page.getByText("sha256:fixture-only-product-journey")).toBeVisible();
});

test("journey D: liuxiang uses authorized records and can honestly return insufficient", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/evidence`, async (route) => route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})}));
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/executions`, async (route) => route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
    id:"run-d",archive_id:"archive-d",status:"insufficient",strength_bp:0,confidence_bp:0,output_hash:"sha256:fixture-output",trace_hash:"sha256:fixture-trace",research_notice:"研究态",candidates:[
      "lx_ming","lx_ye","lx_yuan","lx_meng","lx_yuan_relation","lx_shi"
    ].map((dimension_id,index)=>({dimension_id,rank:index+1,strength_bp:0,confidence_bp:0,status:"insufficient",support_count:0,counterevidence_count:0,missing_facts:["minimum_independent_records"]}))
  })}));
  await page.goto("/consult/liuxiang");
  await expect(page.getByText("未经审校的干支、星曜、卦象解释继续禁用")).toBeVisible();
  await page.getByRole("button",{name:"执行六象研究"}).click();
  await expect(page.getByText("资料不足，暂不成断").first()).toBeVisible();
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
    else await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "retry-record", archive_id: "retry-archive" }) });
  });
  await page.route("**/api/v1/chronicle?*", async (route) => route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[{
    id:"retry-archive",profile_id:profileId,execution_id:null,entry_type:"record",title:"虚构重试记录",status:"recorded",replay_available:false,created_at:"2026-07-29T00:00:00Z",withdrawn:false,
  }]})}));
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

test("topic journey: low-confidence generated identity stays visible and qualified", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/evidence`, async (route) =>
    route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})})
  );
  const ep = (value: unknown, epistemic_status="rule_inferred", confidence_bp=1800) =>
    ({value,epistemic_status,confidence_bp});
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/executions`, async (route) =>
    route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
      id:"topic-synthetic",archive_id:"topic-archive",topic_type:"sushe",
      status:"insufficient",strength_bp:0,confidence_bp:1800,
      graph_hash:"sha256:synthetic-graph",output_hash:"sha256:synthetic-output",
      trace_hash:"sha256:synthetic-trace",research_notice:"三际观原创研究",
      candidates:[{
        candidate_id:"sushe-1",rank:1,status:"insufficient",strength_bp:0,confidence_bp:1800,
        name:ep("沈怀安","generated_identity"),active_era:ep("明末至清初"),
        region_candidates:ep(["江南水运区域"]),identity:ep("地方账房"),
        profession:ep("文书人员"),key_life_events:ep("迁居"),
        death_candidates:[{rank:1,cause:ep("疾病")}],
        reincarnation:{main_value:ep(7),range:ep([6,9])},
        causal_debts:[{debt_id:"d1",type:ep("未竟之诺"),confidence_bp:1200}],
        supporting_record_ids:[],counterevidence_record_ids:[],conflicts:[],missing_facts:["minimum_independent_records"],
      }],
    })})
  );
  await page.goto("/consult/sushe");
  await page.getByRole("button",{name:"开始专题推演"}).click();
  await expect(page.getByRole("heading",{name:"沈怀安【可能·资料不足】"})).toBeVisible();
  await expect(page.getByText("历史人物", {exact:false})).toHaveCount(0);
  await page.getByText("研究详情", {exact:true}).click();
  await expect(page.getByText("sha256:synthetic-output")).toBeVisible();
});

test("life trend journey: gaps, future projection and deterministic report stay distinct", async ({ page }) => {
  await seedSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/life-trend/evidence`, async route =>
    route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({factors:[
      {factor_id:"e1:lx_shi",factor_type:"lx_shi",occurred_on:"2024-03-01",tags:["学习"]},
      {factor_id:"e2:lx_yuan",factor_type:"lx_yuan",occurred_on:"2025-05-01",tags:["持续"]},
    ]})})
  );
  await page.route(`**/api/v1/profiles/${profileId}/life-trend/executions`, async route =>
    route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
      id:"life-trend-synthetic",archive_id:"life-trend-archive",status:"provisional",
      timeline:[
        {bucket_id:"2024",start:"2024-01-01",end:"2024-12-31",segment:"observed_past",candle:{open:0,high:18,low:0,close:18},confidence_bp:6400,coverage_bp:4200,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
        {bucket_id:"2025",start:"2025-01-01",end:"2025-12-31",segment:"observed_past",candle:{open:18,high:25,low:12,close:21},confidence_bp:6500,coverage_bp:4300,status:"contested",auspice:{label:"吉凶相争"},missing:[]},
        {bucket_id:"2026",start:"2026-01-01",end:"2026-12-31",segment:"insufficient_gap",candle:null,confidence_bp:0,coverage_bp:0,status:"insufficient",auspice:{label:"资料不足，暂不定吉凶"},missing:["no_allocated_evidence"]},
        {bucket_id:"2027",start:"2027-01-01",end:"2027-12-31",segment:"projected_future",candle:{open:21,high:24,low:21,close:24},confidence_bp:4100,coverage_bp:2800,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
      ],
      timing_windows:[{window_id:"timing:2027",start:"2027-01-01",end:"2027-12-31",type:"action_window",confidence_bp:4100}],
      report:{chapter:"云开有碍 · 吉中有阻",symbolic_title:"云开有碍",image_text:"长卷依时展开，明处据实落笔，空处仍留白。",plain_interpretation:"这是完全虚构的确定性页面契约。",past:"往际有两段事实窗口。",current:"当下资料留白。",future:"未来为规则推演，可信度递减。",auspice:"吉中有阻",action_guidance:"先处理逆证，再稳步推进。"},
      core_output_hash:"sha256:synthetic-core",deterministic_report_hash:"sha256:synthetic-report",trace_hash:"sha256:synthetic-trace",
    })})
  );
  await page.goto("/consult/life-trend");
  await page.getByRole("button",{name:"生成命势长图与断章"}).click();
  await expect(page.getByRole("heading",{name:"云开有碍 · 吉中有阻"})).toBeVisible();
  const readableTimeline=page.viewportSize()!.width<=767?page.locator(".mobile-buckets"):page.locator(".table-scroll");
  await expect(readableTimeline.getByText("留白",{exact:true})).toBeVisible();
  await expect(readableTimeline.getByText("未来推演",{exact:page.viewportSize()!.width>767})).toBeVisible();
  await expect(page.getByText("人生K线不是证券价格")).toBeVisible();
  if(page.viewportSize()!.width>767)await expect(page.getByText("命势长图文字表格回退")).toBeVisible();
});
