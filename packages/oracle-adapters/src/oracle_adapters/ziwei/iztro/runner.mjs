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
  star_details: [...palace.majorStars, ...palace.minorStars, ...palace.adjectiveStars]
    .map((star) => ({ name: star.name, type: star.type, scope: star.scope,
      brightness: star.brightness ?? null, mutagen: star.mutagen ?? null }))
    .sort((a, b) => a.name < b.name ? -1 : (a.name > b.name ? 1 : 0)),
  decadal: palace.decadal,
  ages: [...palace.ages],
}));
const life = palaces.find((palace) => palace.name === "命宫");
const body = palaces.find((palace) => palace.name === "身宫") ??
  palaces[astrolabe.earthlyBranchOfBodyPalace
    ? palaces.findIndex((palace) => palace.branch === astrolabe.earthlyBranchOfBodyPalace)
    : 0];
const horoscope = value.target_date ? astrolabe.horoscope(value.target_date, value.target_hour_index ?? 0) : null;
const period = (item) => item ? ({ index: item.index, name: item.name,
  heavenly_stem: item.heavenlyStem, earthly_branch: item.earthlyBranch,
  palace_names: item.palaceNames, mutagens: item.mutagen,
  stars: item.stars.map((group) => group.map((star) => ({name: star.name, type: star.type, scope: star.scope}))) }) : null;
process.stdout.write(JSON.stringify({
  execution_status: "success",
  unsupported_features: [],
  warnings: ["iztro is an external differential oracle, not an engine authority"],
  life_palace_branch: life?.branch ?? null,
  body_palace_branch: astrolabe.earthlyBranchOfBodyPalace ?? body?.branch ?? null,
  five_element_bureau: astrolabe.fiveElementsClass,
  soul_ruler: astrolabe.soul,
  body_ruler: astrolabe.body,
  solar_date: astrolabe.solarDate,
  lunar_date: astrolabe.lunarDate,
  palaces,
  horoscope: horoscope ? { solar_date: horoscope.solarDate, lunar_date: horoscope.lunarDate,
    decadal: period(horoscope.decadal), yearly: period(horoscope.yearly),
    monthly: period(horoscope.monthly), daily: period(horoscope.daily), hourly: period(horoscope.hourly) } : null,
}));
