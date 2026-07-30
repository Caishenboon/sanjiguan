import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const baseURL = process.env.SANJI_PREVIEW_URL || "http://127.0.0.1:3000";
const output = resolve(process.cwd(), "../../outputs/sprint18");
await mkdir(output, { recursive: true });
const browser = await chromium.launch();

const run = {
  id: "synthetic-life-trend", archive_id: "synthetic-archive", status: "provisional",
  timeline: [
    {bucket_id:"2024",start:"2024-01-01",end:"2024-12-31",segment:"observed_past",candle:{open:0,high:1800,low:0,close:1800},confidence_bp:6400,coverage_bp:4200,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
    {bucket_id:"2025",start:"2025-01-01",end:"2025-12-31",segment:"observed_past",candle:{open:1800,high:2500,low:1200,close:2100},confidence_bp:6500,coverage_bp:4300,status:"contested",auspice:{label:"吉凶相争"},missing:[]},
    {bucket_id:"2026",start:"2026-01-01",end:"2026-12-31",segment:"insufficient_gap",candle:null,confidence_bp:0,coverage_bp:0,status:"insufficient",auspice:{label:"资料不足，暂不定吉凶"},missing:["no_allocated_evidence"]},
    {bucket_id:"2027",start:"2027-01-01",end:"2027-12-31",segment:"projected_future",candle:{open:2100,high:2400,low:2100,close:2400},confidence_bp:4100,coverage_bp:2800,status:"provisional",auspice:{label:"吉中有阻"},missing:[]},
  ],
  timing_windows: [{window_id:"timing:2027",start:"2027-01-01",end:"2027-12-31",type:"action_window",confidence_bp:4100}],
  report: {
    chapter:"云开有碍 · 吉中有阻",symbolic_title:"云开有碍",
    image_text:"长卷依时展开，明处据实落笔，空处仍留白。",
    plain_interpretation:"这是完全虚构的确定性页面契约；未来窗口只展示规则推演。",
    past:"往际有两段事实窗口。",current:"当下资料留白。",
    future:"未来为规则推演，可信度随距离递减。",auspice:"吉中有阻",
    action_guidance:"先处理逆证，再在已核实条件内稳步推进。",
  },
  core_output_hash:"sha256:synthetic-core",deterministic_report_hash:"sha256:synthetic-report",
  trace_hash:"sha256:synthetic-trace",
};

for (const [name, viewport] of [
  ["desktop", { width: 1440, height: 1100 }],
  ["mobile", { width: 390, height: 844 }],
]) {
  const context = await browser.newContext({ viewport, colorScheme: "dark", locale: "zh-CN" });
  const page = await context.newPage();
  await page.route("**/api/v1/profiles/*/life-trend/evidence", route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ factors: [
      {factor_id:"e1:lx_shi",factor_type:"lx_shi",occurred_on:"2024-03-01",tags:["学习"]},
      {factor_id:"e2:lx_yuan",factor_type:"lx_yuan",occurred_on:"2025-05-01",tags:["持续"]},
    ]}) })
  );
  await page.route("**/api/v1/profiles/*/life-trend/executions", route =>
    route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(run) })
  );
  await page.goto(baseURL);
  await page.evaluate(() => sessionStorage.setItem("sanjiguan:product-session:v1", JSON.stringify({
    subject: {id:"019fa02b-a48f-7bb0-8a18-900000000001",name:"虚构测试主体",birthDate:"1990-01-01",timePrecision:"unknown"},
  })));
  await page.goto(`${baseURL}/consult/life-trend`);
  await page.getByRole("button", { name: "生成命势长图与断章" }).click();
  await page.getByRole("heading", { name: "云开有碍 · 吉中有阻" }).waitFor();
  await page.screenshot({ path: resolve(output, `life-trend-${name}.png`), fullPage: true });
  await context.close();
}
await browser.close();
console.log(`Sprint 18 synthetic screenshots written to ${output}`);
