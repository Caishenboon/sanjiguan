import { astro } from "iztro";

let input = "";
for await (const chunk of process.stdin) input += chunk;
const value = JSON.parse(input);
const gender = value.traditional_sex === "male" ? "男" : "女";
const date = `${value.lunar_year}-${Math.abs(value.lunar_month)}-${value.lunar_day}`;
const astrolabe = astro.byLunar(
  date,
  value.hour_index,
  gender,
  value.lunar_month < 0,
  true,
  "zh-CN",
);
const palaces = astrolabe.palaces.map((palace, index) => ({
  index,
  name: palace.name,
  branch: palace.earthlyBranch,
  heavenly_stem: palace.heavenlyStem,
  major_stars: palace.majorStars.map((star) => star.name).sort(),
}));
const life = palaces.find((palace) => palace.name === "命宫");
const body = palaces.find((palace) => palace.name === "身宫") ??
  palaces[astrolabe.earthlyBranchOfBodyPalace
    ? palaces.findIndex((palace) => palace.branch === astrolabe.earthlyBranchOfBodyPalace)
    : 0];
process.stdout.write(JSON.stringify({
  execution_status: "success",
  unsupported_features: [],
  warnings: ["iztro is an external differential oracle, not an engine authority"],
  life_palace_branch: life?.branch ?? null,
  body_palace_branch: astrolabe.earthlyBranchOfBodyPalace ?? body?.branch ?? null,
  five_element_bureau: astrolabe.fiveElementsClass,
  palaces,
}));
