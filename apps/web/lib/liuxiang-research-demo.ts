export const liuxiangDimensions = [
  {id:"lx_ming",name:"命象",strength:9200,confidence:7800,independent:3,counter:1},
  {id:"lx_ye",name:"业象",strength:6400,confidence:7200,independent:2,counter:1},
  {id:"lx_yuan",name:"愿象",strength:7100,confidence:6600,independent:2,counter:2},
  {id:"lx_meng",name:"梦象",strength:2800,confidence:3100,independent:1,counter:1},
  {id:"lx_yuan_relation",name:"缘象",strength:4300,confidence:3900,independent:1,counter:2},
  {id:"lx_shi",name:"世象",strength:6900,confidence:8100,independent:3,counter:1},
] as const;

export const evidenceChain = [
  ["原始记录","完全虚构的合成记录"],
  ["机械事实","已版本化字段；不含解释"],
  ["Mapping","LX.SYNTHETIC.CONFORMANCE.V1"],
  ["Signal v2","整数基点与来源指纹"],
  ["独立组","同源仅保留最强贡献"],
  ["候选","Strength 与 Confidence 分离"],
  ["状态","provisional"],
] as const;

export const researchSources = [
  {
    name:"VedAstro 出生资料",revision:"c864548…",license:"条件允许本地研究",
    rows:"15,807",precision:"精确时刻 15,807；IANA 时区缺失 15,807",
    shared:"vedastro_org",enabled:false,
  },
  {
    name:"VedAstro 婚恋事件",revision:"2c297bc…",license:"条件允许本地研究",
    rows:"人物 15,807 · 事件 18,148",precision:"结婚精确日 11,080 · 仅年份 5,664",
    shared:"vedastro_org",enabled:false,
  },
  {
    name:"DreamBank 英文梦境",revision:"d400ee8…",license:"license_review_required",
    rows:"未下载正文",precision:"授权链未闭环",shared:"dreambank_repackaged",enabled:false,
  },
] as const;
