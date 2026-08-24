import type { ReactNode } from "react";

export type InstrumentMode = "yijing" | "bazi" | "ziwei" | "liuxiang" | "sushe" | "zhongyin" | "yuanqi" | "life-trend";

export type InstrumentItem = {
  label: string;
  value: string;
  state?: "active" | "moving" | "future" | "missing" | "counter";
};

const MODE_COPY: Record<InstrumentMode,{mark:string;english:string}> = {
  yijing:{mark:"易",english:"HEXAGRAM INSTRUMENT"},
  bazi:{mark:"命",english:"FOUR PILLARS INSTRUMENT"},
  ziwei:{mark:"微",english:"PALACE INSTRUMENT"},
  liuxiang:{mark:"象",english:"EVIDENCE ORBIT"},
  sushe:{mark:"世",english:"CANDIDATE STAR MAP"},
  zhongyin:{mark:"间",english:"TRANSITION GATE"},
  yuanqi:{mark:"缘",english:"RELATIONSHIP KNOT"},
  "life-trend":{mark:"势",english:"LIFE TREND CHRONOMETER"},
};

export default function ObservationInstrument({mode,title,items=[],caption,children}:{mode:InstrumentMode;title:string;items?:InstrumentItem[];caption:string;children?:ReactNode}) {
  const copy=MODE_COPY[mode];
  return <figure className="observation-instrument" data-mode={mode}>
    <div className="instrument-frame" aria-hidden="true"><i/><i/><i/><span/><span/></div>
    <header><small>{copy.english}</small><b>{title}</b></header>
    {mode==="yijing"&&<div className="instrument-hexagram" aria-hidden="true">{items.slice(0,6).reverse().map((item,index)=><span key={`${item.label}-${index}`} data-yin={item.value.includes("阴")} data-moving={item.state==="moving"}/>)}</div>}
    {mode==="bazi"&&<div className="instrument-pillars" aria-hidden="true">{items.slice(0,4).map((item)=><span key={item.label}><small>{item.label}</small><b>{item.value.slice(0,1)||"·"}</b><em>{item.value.slice(1,2)||"·"}</em></span>)}</div>}
    {mode==="ziwei"&&<div className="instrument-palaces" aria-hidden="true">{Array.from({length:12},(_,index)=><i key={index}/>)}<b>{copy.mark}</b></div>}
    {!["yijing","bazi","ziwei"].includes(mode)&&<div className="instrument-orbit" aria-hidden="true"><b>{copy.mark}</b>{items.slice(0,6).map((item,index)=><span className={`instrument-node instrument-node--${index+1}`} data-state={item.state||"active"} key={`${item.label}-${index}`}><small>{item.label}</small><em>{item.value}</em></span>)}</div>}
    {items.length>0&&<dl className="instrument-legend">{items.slice(0,6).map((item,index)=><div key={`${item.label}-${index}`}><dt>{item.label}</dt><dd>{item.value}</dd></div>)}</dl>}
    {children}
    <figcaption>{caption}</figcaption>
  </figure>;
}

export function RitualProgress({steps,current}:{steps:string[];current:number}){
  return <div className="ritual-progress ritual-progress--staged" role="status" aria-live="polite">
    {steps.map((step,index)=><span key={step} data-state={index<current?"done":index===current?"current":"waiting"}><i>{index<current?"✓":String(index+1).padStart(2,"0")}</i>{step}</span>)}
  </div>;
}
