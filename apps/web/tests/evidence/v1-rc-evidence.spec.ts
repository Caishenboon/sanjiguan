import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const profileId = "019f9f61-5dc9-79cf-8b92-0000000000e1";
const evidenceDir = path.resolve(process.cwd(), "../../docs/product/evidence/screenshots");

async function seedSyntheticSubject(page: Page) {
  await page.addInitScript(({ id }) => {
    sessionStorage.setItem("sanjiguan:product-session:v1", JSON.stringify({
      subject: { id, name: "虚构体验主体", birthDate: "1990-01-01", timePrecision: "unknown" },
      chronicles: [],
    }));
  }, { id: profileId });
}

async function routeLifeTrend(page: Page) {
  await page.route(`**/api/v1/profiles/${profileId}/life-trend/evidence`, async route =>
    route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({factors:[
      {factor_id:"synthetic-event:lx_shi",factor_type:"lx_shi",occurred_on:"2024-03-01",tags:["虚构学习事件"]},
      {factor_id:"synthetic-vow:lx_yuan",factor_type:"lx_yuan",occurred_on:"2025-05-01",tags:["虚构持续愿向"]},
    ]})})
  );
  await page.route(`**/api/v1/profiles/${profileId}/life-trend/executions`, async route =>
    route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
      id:"life-trend-synthetic-evidence",archive_id:"archive-synthetic-evidence",status:"provisional",
      timeline:[
        {bucket_id:"2024",start:"2024-01-01",end:"2024-12-31",segment:"observed_past",candle:{open:0,high:1800,low:0,close:1800},confidence_bp:6400,coverage_bp:4200,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
        {bucket_id:"2025",start:"2025-01-01",end:"2025-12-31",segment:"observed_past",candle:{open:1800,high:2500,low:1200,close:2100},confidence_bp:6500,coverage_bp:4300,status:"contested",auspice:{label:"吉凶相争"},missing:[]},
        {bucket_id:"2026",start:"2026-01-01",end:"2026-12-31",segment:"insufficient_gap",candle:null,confidence_bp:0,coverage_bp:0,status:"insufficient",auspice:{label:"资料不足，暂不定吉凶"},missing:["no_allocated_evidence"]},
        {bucket_id:"2027",start:"2027-01-01",end:"2027-12-31",segment:"projected_future",candle:{open:2100,high:2400,low:2100,close:2400},confidence_bp:4100,coverage_bp:2800,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
      ],
      timing_windows:[{window_id:"timing:2027",start:"2027-01-01",end:"2027-12-31",type:"action_window",confidence_bp:4100}],
      report:{chapter:"云开有碍 · 吉中有阻",symbolic_title:"云开有碍",image_text:"长卷依时展开，明处据实落笔，空处仍留白。",plain_interpretation:"这是完全虚构的确定性模板报告。",past:"往际有两段虚构事实窗口。",current:"当下资料留白。",future:"未来为规则推演，可信度按规则递减。",auspice:"吉中有阻",action_guidance:"先处理逆证，再稳步推进。"},
      core_output_hash:"sha256:synthetic-core-evidence",deterministic_report_hash:"sha256:synthetic-report-evidence",trace_hash:"sha256:synthetic-trace-evidence",
    })})
  );
}

async function openLifeTrend(page: Page) {
  await seedSyntheticSubject(page);
  await routeLifeTrend(page);
  await page.goto("/consult/life-trend");
  await page.getByRole("button", {name:"生成命势长图与三际断章"}).click();
  await expect(page.getByRole("heading", {name:"云开有碍 · 吉中有阻"})).toBeVisible();
  await expect(page.getByText("这是完全虚构的确定性模板报告。").first()).toBeVisible();
}

test("1440 desktop three-period report", async ({ page }) => {
  await page.setViewportSize({width:1440,height:1100});
  await openLifeTrend(page);
  await page.screenshot({path:path.join(evidenceDir,"v1-ux-report-desktop-1440.png"),fullPage:true});
});

test("768 tablet life trend", async ({ page }) => {
  await page.setViewportSize({width:768,height:1024});
  await openLifeTrend(page);
  await page.screenshot({path:path.join(evidenceDir,"v1-ux-life-trend-tablet-768.png"),fullPage:true});
});

test("1920 wide past-life candidate", async ({ page }) => {
  await page.setViewportSize({width:1920,height:1080});
  await seedSyntheticSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/evidence`, async route =>
    route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})}));
  const ep=(value:unknown,epistemic_status="rule_inferred",confidence_bp=1800)=>({value,epistemic_status,confidence_bp});
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/executions`, async route =>
    route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
      id:"topic-synthetic-evidence",archive_id:"topic-archive-evidence",topic_type:"sushe",status:"insufficient",strength_bp:0,confidence_bp:1800,
      graph_hash:"sha256:synthetic-graph-evidence",output_hash:"sha256:synthetic-topic-evidence",trace_hash:"sha256:synthetic-topic-trace",research_notice:"三际观原创研究",
      candidates:[{candidate_id:"sushe-evidence-1",rank:1,status:"insufficient",strength_bp:0,confidence_bp:1800,name:ep("沈怀安","generated_identity"),active_era:ep("明末至清初"),region_candidates:ep(["江南水运区域"]),identity:ep("地方账房"),profession:ep("文书人员"),key_life_events:ep("迁居"),death_candidates:[{rank:1,cause:ep("疾病")}],reincarnation:{main_value:ep(7),range:ep([6,9])},causal_debts:[{debt_id:"synthetic-debt",type:ep("未竟之诺"),confidence_bp:1200}],supporting_record_ids:[],counterevidence_record_ids:[],conflicts:[],missing_facts:["minimum_independent_records"]}],
    })}));
  await page.goto("/consult/sushe");
  await page.getByRole("button",{name:"开始专题推演"}).click();
  await expect(page.getByRole("heading",{name:"沈怀安【可能·资料不足】"})).toBeVisible();
  await page.screenshot({path:path.join(evidenceDir,"v1-ux-sushe-wide-1920.png"),fullPage:true});
});

test("390 mobile record creation", async ({ page }) => {
  await page.setViewportSize({width:390,height:844});
  await page.goto("/onboarding");
  await page.getByLabel("如何称呼这个主体").fill("虚构体验主体");
  await page.getByLabel("出生日期").fill("1990-01-01");
  await page.getByLabel("出生时刻未知").check();
  await page.getByLabel("出生地点原文").fill("虚构城市");
  await page.getByLabel("经度").fill("121.473700");
  await page.getByLabel("纬度").fill("31.230400");
  await page.screenshot({path:path.join(evidenceDir,"v1-ux-onboarding-mobile-390.png"),fullPage:true});
});

test("insufficient liuxiang state", async ({ page }) => {
  await page.setViewportSize({width:1440,height:1100});
  await seedSyntheticSubject(page);
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/evidence`, async route =>
    route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})}));
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/executions`, async route =>
    route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({
      id:"liuxiang-synthetic-evidence",archive_id:"liuxiang-archive-evidence",status:"insufficient",strength_bp:0,confidence_bp:0,output_hash:"sha256:synthetic-liuxiang-evidence",trace_hash:"sha256:synthetic-liuxiang-trace",research_notice:"研究态",
      candidates:["lx_ming","lx_ye","lx_yuan","lx_meng","lx_yuan_relation","lx_shi"].map((dimension_id,index)=>({dimension_id,rank:index+1,strength_bp:0,confidence_bp:0,status:"insufficient",support_count:0,counterevidence_count:0,missing_facts:["minimum_independent_records"]})),
    })}));
  await page.goto("/consult/liuxiang");
  await page.getByRole("button",{name:"起一卷六象合参"}).click();
  await expect(page.getByText("证契未足，不成断").first()).toBeVisible();
  await page.screenshot({path:path.join(evidenceDir,"v1-ux-insufficient-liuxiang-1440.png"),fullPage:true});
});

test("deterministic report without provider", async ({ page }) => {
  await page.setViewportSize({width:1440,height:1100});
  let providerCalls=0;
  await page.route("**/*deepseek*", async route=>{providerCalls+=1;await route.abort("blockedbyclient")});
  await openLifeTrend(page);
  expect(providerCalls).toBe(0);
  await page.locator(".report-reader").screenshot({path:path.join(evidenceDir,"v1-ux-deterministic-report-no-ai-1440.png")});
});

test("home desktop", async ({page})=>{await page.setViewportSize({width:1440,height:1100});await page.goto("/");await expect(page.getByRole("heading",{name:"从如实立卷开始"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-home-desktop-1440.png"),fullPage:true});});
test("home mobile", async ({page})=>{await page.setViewportSize({width:390,height:844});await page.goto("/");await expect(page.getByRole("navigation",{name:"普通用户手机主导航"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-home-mobile-390.png"),fullPage:true});});
test("onboarding desktop", async ({page})=>{await page.setViewportSize({width:1440,height:1100});await page.goto("/onboarding");await expect(page.getByText("第 1—3 步，共 8 步")).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-onboarding-desktop-1440.png"),fullPage:true});});
test("report mobile", async ({page})=>{await page.setViewportSize({width:390,height:844});await openLifeTrend(page);await page.screenshot({path:path.join(evidenceDir,"v1-ux-report-mobile-390.png"),fullPage:true});});

async function routeTopic(page:Page,topic:"zhongyin_life"|"yuanqi"){
  await page.route(`**/api/v1/profiles/${profileId}/topics/${topic}/evidence`,async route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})}));
  const ep=(value:unknown,epistemic_status="rule_inferred",confidence_bp=4300)=>({value,epistemic_status,confidence_bp});
  await page.route(`**/api/v1/profiles/${profileId}/topics/${topic}/executions`,async route=>route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({id:`${topic}-synthetic`,archive_id:`${topic}-archive`,topic_type:topic,status:"provisional",strength_bp:5200,confidence_bp:4300,graph_hash:"sha256:synthetic-graph",output_hash:"sha256:synthetic-output",trace_hash:"sha256:synthetic-trace",research_notice:"三际观原创研究",candidates:[topic==="yuanqi"?{candidate_id:"yuanqi-1",rank:1,status:"provisional",strength_bp:5200,confidence_bp:4300,observation_scope:"unilateral_observation",relationship_stage:ep("关系维持"),future_trend:ep("关系仍需以实际行动确认"),past_life_identity_candidates:[{side:"subject",name:ep("顾清河","generated_identity")}],supporting_record_ids:["synthetic-1"],counterevidence_record_ids:["synthetic-2"],conflicts:["承诺与行动不同步"],missing_facts:["双方同意"]}:{candidate_id:"zhongyin-1",rank:1,status:"provisional",strength_bp:5200,confidence_bp:4300,transition_state:ep("新结构萌生"),old_structure:ep(["旧工作节奏"]),new_structure_clues:ep(["新的学习计划"]),unfinished_matters:ep(["交接尚未完成"]),supporting_record_ids:["synthetic-1"],counterevidence_record_ids:["synthetic-2"],conflicts:[],missing_facts:["持续行动记录"]}]})}));
}
test("zhongyin gate",async({page})=>{await page.setViewportSize({width:1440,height:1100});await seedSyntheticSubject(page);await routeTopic(page,"zhongyin_life");await page.goto("/consult/zhongyin");await page.getByRole("button",{name:"开始专题推演"}).click();await page.screenshot({path:path.join(evidenceDir,"v1-ux-zhongyin-1440.png"),fullPage:true});});
test("yuanqi consent",async({page})=>{await page.setViewportSize({width:1440,height:1100});await seedSyntheticSubject(page);await routeTopic(page,"yuanqi");await page.goto("/consult/yuanqi");await page.getByRole("button",{name:"开始专题推演"}).click();await page.screenshot({path:path.join(evidenceDir,"v1-ux-yuanqi-1440.png"),fullPage:true});});

async function routeLiuxiang(page:Page,status:"provisional"|"contested"){
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/evidence`,async route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({items:[]})}));
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/executions`,async route=>route.fulfill({status:201,contentType:"application/json",body:JSON.stringify({id:`liuxiang-${status}`,archive_id:`liuxiang-${status}-archive`,status,strength_bp:status==="contested"?6100:6800,confidence_bp:status==="contested"?5200:6400,output_hash:"sha256:synthetic-liuxiang",trace_hash:"sha256:synthetic-trace",research_notice:"研究态",candidates:["lx_yuan","lx_ye","lx_shi","lx_meng","lx_ming","lx_yuan_relation"].map((dimension_id,index)=>({dimension_id,rank:index+1,strength_bp:Math.max(1200,6800-index*650),confidence_bp:Math.max(1800,6400-index*500),status:status==="contested"&&index<2?"contested":"provisional",support_count:3-index%2,counterevidence_count:index%2,missing_facts:index>3?["minimum_time_span"]:[]}))})}));
}
test("liuxiang desktop",async({page})=>{await page.setViewportSize({width:1440,height:1100});await seedSyntheticSubject(page);await routeLiuxiang(page,"provisional");await page.goto("/consult/liuxiang");await page.getByRole("button",{name:"起一卷六象合参"}).click();await page.screenshot({path:path.join(evidenceDir,"v1-ux-liuxiang-desktop-1440.png"),fullPage:true});});
test("contested liuxiang",async({page})=>{await page.setViewportSize({width:1440,height:1100});await seedSyntheticSubject(page);await routeLiuxiang(page,"contested");await page.goto("/consult/liuxiang");await page.getByRole("button",{name:"起一卷六象合参"}).click();await expect(page.getByText("两象相争").first()).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-contested-1440.png"),fullPage:true});});
test("delete confirmation",async({page})=>{await page.setViewportSize({width:1440,height:1100});await page.goto("/me/data");await page.getByRole("button",{name:"删除账号及私人数据"}).click();await expect(page.getByRole("dialog",{name:"确认彻底删除？"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-delete-confirmation-1440.png"),fullPage:true});});
test("permission denied",async({page})=>{await page.setViewportSize({width:1440,height:1100});await page.goto("/forbidden");await expect(page.getByRole("heading",{name:"研究后台只对授权角色开放"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-ux-forbidden-1440.png"),fullPage:true});});

test("owner sign in",async({page})=>{await page.setViewportSize({width:1440,height:1000});await page.goto("/start");await expect(page.getByRole("button",{name:"建立所有者并继续"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-owner-login-1440.png"),fullPage:true});});
test("invitation entry",async({page})=>{await page.setViewportSize({width:1440,height:1000});await page.goto("/start");await page.getByRole("button",{name:"使用邀请进入"}).click();await expect(page.getByRole("button",{name:"接受邀请并进入"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-invitation-1440.png"),fullPage:true});});
test("record center",async({page})=>{await page.setViewportSize({width:1440,height:1000});await seedSyntheticSubject(page);await page.goto("/records");await expect(page.getByRole("heading",{name:"这次想记录什么？"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-record-center-1440.png"),fullPage:true});});
test("three coin mechanical entry",async({page})=>{await page.setViewportSize({width:1440,height:1000});await seedSyntheticSubject(page);await page.goto("/consult/yijing");await expect(page.getByRole("heading",{name:"录入实物三钱"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-yijing-three-coin-1440.png"),fullPage:true});});
test("bazi unknown-time boundary",async({page})=>{await page.setViewportSize({width:1440,height:1000});await seedSyntheticSubject(page);await page.route(`**/api/v1/profiles/${profileId}`,async route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify({id:profileId,birth_record_status:"confirmed",birth:{calendar_type:"gregorian",local_date:"1990-01-01",local_time:null,timezone_id:"Asia/Shanghai",time_precision:"unknown",place:{longitude:121.4737}}})}));await page.goto("/consult/bazi");await expect(page.getByRole("heading",{name:"出生时刻未知，暂不生成完整四柱"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-bazi-unknown-time-1440.png"),fullPage:true});});
test("ziwei research input",async({page})=>{await page.setViewportSize({width:1440,height:1000});await seedSyntheticSubject(page);await page.goto("/consult/ziwei");await expect(page.getByRole("heading",{name:"紫微三合研究结构"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-ziwei-research-1440.png"),fullPage:true});});
test("network offline state",async({page})=>{await page.setViewportSize({width:390,height:844});await page.goto("/offline");await expect(page.getByRole("heading",{name:"暂时无法连接三际观服务"})).toBeVisible();await page.screenshot({path:path.join(evidenceDir,"v1-1-network-offline-390.png"),fullPage:true});});
