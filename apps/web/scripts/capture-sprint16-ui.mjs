import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..", "..", "..");
const out = resolve(root, "docs", "screenshots");
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ headless: true });
const profileId = "019f9f61-5dc9-79cf-8b92-000000000001";
const evidence = [
  ["lx_ming", "coverage", "profile"],
  ["lx_yuan", "evidence", "vow-1"],
  ["lx_yuan", "evidence", "vow-2"],
  ["lx_shi", "evidence", "event-1"],
].map(([dimension_id, fact_kind, record_id]) => ({
  record_id, record_table: record_id === "profile" ? "profiles" : "journal_entries",
  dimension_id, fact_kind, withdrawn: false, date_precision: "exact_date", state: "sustained",
}));
const candidates = ["lx_yuan", "lx_shi", "lx_ming", "lx_ye", "lx_meng", "lx_yuan_relation"].map(
  (dimension_id, index) => ({
    dimension_id, rank: index + 1,
    strength_bp: index === 0 ? 3120 : index === 1 ? 1400 : 0,
    confidence_bp: index === 0 ? 5820 : index === 1 ? 4310 : 2100,
    status: index === 0 ? "provisional" : "insufficient",
    support_count: index === 0 ? 2 : index === 1 ? 1 : 0,
    counterevidence_count: 0,
    missing_facts: index > 1 ? ["minimum_independent_records"] : [],
  }),
);
const run = {
  id: "019f9f61-5dc9-79cf-8b92-000000000016",
  archive_id: "019f9f61-5dc9-79cf-8b92-000000000017",
  status: "provisional", strength_bp: 3120, confidence_bp: 5820, candidates,
  output_hash: "sha256:synthetic-ui-review-output-not-a-golden-hash",
  trace_hash: "sha256:synthetic-ui-review-trace-not-a-golden-hash",
  research_notice: "三际观原创研究体系 · UNCONFIRMED · 不可生产激活",
};

async function seed(page) {
  await page.addInitScript(({ profileId }) => {
    sessionStorage.setItem("sanjiguan:product-session:v1", JSON.stringify({
      subject: { id: profileId, name: "完全虚构体验主体", birthDate: "1990-01-01", timePrecision: "unknown" },
    }));
  }, { profileId });
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/evidence`, route =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ items: evidence }) }));
  await page.route(`**/api/v1/profiles/${profileId}/liuxiang/executions`, route =>
    route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify(run) }));
}

const desktop = await browser.newPage({ viewport: { width: 1440, height: 1050 }, colorScheme: "dark" });
await seed(desktop);
await desktop.goto("http://127.0.0.1:3000/consult/liuxiang");
await desktop.getByRole("button", { name: "执行六象研究" }).click();
await desktop.screenshot({ path: resolve(out, "sprint16-liuxiang-desktop.png"), fullPage: true });

const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, colorScheme: "dark" });
await seed(mobile);
await mobile.route("**/api/v1/chronicle?*", route => route.fulfill({
  status: 200, contentType: "application/json", body: JSON.stringify({ items: [{
    id: run.archive_id, profile_id: profileId, execution_id: run.id,
    entry_type: "liuxiang_research", title: "六象真实证据研究",
    status: "provisional", candidate_summary: candidates, replay_available: true,
    created_at: "2026-07-29T00:00:00Z", withdrawn: false,
  }] }),
}));
await mobile.goto("http://127.0.0.1:3000/chronicle");
await mobile.screenshot({ path: resolve(out, "sprint16-chronicle-mobile.png"), fullPage: true });
await browser.close();
