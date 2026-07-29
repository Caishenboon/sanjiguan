import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..", "..", "..");
const out = resolve(root, "docs", "screenshots");
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const profileId = "019fa02b-a48f-7bb0-8a17-000000000017";
const ep = (value, epistemic_status = "rule_inferred", confidence_bp = 2400) =>
  ({ value, epistemic_status, confidence_bp });
const candidate = {
  candidate_id: "sushe-1", rank: 1, status: "insufficient",
  strength_bp: 1700, confidence_bp: 2400,
  name: ep("沈怀安", "generated_identity"), active_era: ep("明末至清初"),
  region_candidates: ep(["江南水运区域", "苏州府周边"]),
  identity: ep("地方商户家族中的账房与文书"),
  profession: ep("文书人员"), key_life_events: ep("迁居或远行"),
  death_candidates: [{ rank: 1, cause: ep("疾病") }, { rank: 2, cause: ep("原因不明") }],
  reincarnation: { main_value: ep(7), range: ep([6, 9]) },
  causal_debts: [{ debt_id: "debt-1", type: ep("未竟之诺"), confidence_bp: 1600 }],
  supporting_record_ids: ["synthetic-vow"], counterevidence_record_ids: [],
  conflicts: [], missing_facts: ["independent_historical_source"],
};
const run = {
  id: "019fa02b-a48f-7bb0-8a17-000000000018",
  archive_id: "019fa02b-a48f-7bb0-8a17-000000000019",
  topic_type: "sushe", status: "insufficient", strength_bp: 1700, confidence_bp: 2400,
  candidates: [candidate], graph_hash: "sha256:synthetic-ui-graph",
  output_hash: "sha256:synthetic-ui-output", trace_hash: "sha256:synthetic-ui-trace",
  research_notice: "三际观原创研究 · UNCONFIRMED · 不可生产激活",
};

async function prepare(viewport) {
  const page = await browser.newPage({ viewport, colorScheme: "dark" });
  await page.addInitScript(({ profileId }) => {
    sessionStorage.setItem("sanjiguan:product-session:v1", JSON.stringify({
      subject: { id: profileId, name: "完全虚构体验主体", birthDate: "1990-01-01", timePrecision: "unknown" },
    }));
  }, { profileId });
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/evidence`, route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
      items: [{ record_id: "synthetic-vow", node_type: "vow", tags: ["持续行动"], withdrawn: false }],
    }) }));
  await page.route(`**/api/v1/profiles/${profileId}/topics/sushe/executions`, route =>
    route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(run) }));
  await page.goto("http://127.0.0.1:3000/consult/sushe");
  await page.getByRole("button", { name: "开始专题推演" }).click();
  await page.getByRole("heading", { name: "沈怀安【可能·资料不足】" }).waitFor();
  return page;
}

const desktop = await prepare({ width: 1440, height: 1050 });
await desktop.screenshot({ path: resolve(out, "sprint17-sushe-desktop.png"), fullPage: true });
const mobile = await prepare({ width: 390, height: 844 });
await mobile.screenshot({ path: resolve(out, "sprint17-sushe-mobile.png"), fullPage: true });
await browser.close();
