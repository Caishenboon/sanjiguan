export type ProductTerm = {
  label: string;
  explanation: string;
  technicalValue: string;
  pages: string[];
  researchOnly: boolean;
};

export const PRODUCT_TERMS: Record<string, ProductTerm> = {
  strength: {
    label: "象势强度",
    explanation: "现有有效资料对某一方向的支持力度，不代表资料一定完整。",
    technicalValue: "strength",
    pages: ["六象研究详情", "候选比较"],
    researchOnly: false,
  },
  confidence: {
    label: "证据可信度",
    explanation: "综合来源、完整度、独立性、分歧与边界稳定性后的可信程度。",
    technicalValue: "confidence",
    pages: ["六象研究详情", "候选比较"],
    researchOnly: false,
  },
  decisive: {
    label: "象意较明",
    explanation: "领先、资料完整度与证据可信度同时达到研究规则门槛。",
    technicalValue: "decisive",
    pages: ["结果", "三际录"],
    researchOnly: false,
  },
  provisional: {
    label: "初见其象",
    explanation: "已有较明显方向，但关键资料或独立证据仍需补充。",
    technicalValue: "provisional",
    pages: ["结果", "三际录"],
    researchOnly: false,
  },
  contested: {
    label: "诸象相争",
    explanation: "多个方向接近，或正证、逆证之间仍有明显冲突。",
    technicalValue: "contested",
    pages: ["结果", "三际录"],
    researchOnly: false,
  },
  insufficient: {
    label: "资料不足，暂不成断",
    explanation: "现有资料不足以形成负责任的研究判断。",
    technicalValue: "insufficient",
    pages: ["结果", "合参"],
    researchOnly: false,
  },
  counterevidence: {
    label: "逆证",
    explanation: "与当前方向相反、可降低支持力度的资料。",
    technicalValue: "counterevidence",
    pages: ["结果", "研究详情"],
    researchOnly: false,
  },
  missingness: {
    label: "尚缺资料",
    explanation: "本次分析仍未取得、未知或不适用的资料。",
    technicalValue: "missingness",
    pages: ["结果", "首页"],
    researchOnly: false,
  },
  boundary_sensitivity: {
    label: "边界敏感",
    explanation: "时间或规则边界变化可能让机械结构发生变化。",
    technicalValue: "boundary_sensitivity",
    pages: ["八字结果", "研究详情"],
    researchOnly: false,
  },
  profile_dispute: {
    label: "规则方案存在分歧",
    explanation: "不同已登记规则方案产生了不同机械结果，系统不会隐藏选择默认。",
    technicalValue: "profile dispute",
    pages: ["八字结果", "紫微结果"],
    researchOnly: false,
  },
  replay: {
    label: "按原版本重放",
    explanation: "使用当时保存的输入、引擎与规则版本复现原结果。",
    technicalValue: "replay",
    pages: ["三际录详情", "研究详情"],
    researchOnly: false,
  },
  reanalyze: {
    label: "用当前版本重新分析",
    explanation: "保留旧结果，另建一次使用当前版本的新执行。",
    technicalValue: "reanalyze",
    pages: ["三际录详情"],
    researchOnly: false,
  },
};

export function productStatus(value: string) {
  return PRODUCT_TERMS[value]?.label ?? value;
}
