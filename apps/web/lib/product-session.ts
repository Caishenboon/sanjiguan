"use client";

export type SubjectSummary = {
  id: string;
  name: string;
  birthDate: string;
  timePrecision: "minute" | "double_hour" | "half_day" | "unknown";
};

export type ChronicleSummary = {
  id: string;
  profileId: string;
  date: string;
  subject: string;
  type: "记录" | "易经" | "八字" | "紫微" | "六象研究";
  title: string;
  status: string;
  source: string;
  replayable: boolean;
};

export type ToolRunSummary = {
  id: string;
  tool: "yijing" | "bazi" | "ziwei";
  title: string;
  completedAt: string;
  result: Record<string, unknown>;
};

export type ProductSession = {
  subject?: SubjectSummary;
  /** Compatibility-only display cache. PostgreSQL `/api/v1/chronicle` is authoritative. */
  chronicles: ChronicleSummary[];
  recentRun?: ToolRunSummary;
  pendingTask?: { label: string; href: string };
};

const KEY = "sanjiguan:product-session:v1";
const EMPTY: ProductSession = { chronicles: [] };

export function readProductSession(): ProductSession {
  if (typeof window === "undefined") return EMPTY;
  try {
    const parsed = JSON.parse(sessionStorage.getItem(KEY) || "{}");
    // Browser storage is only an interaction cache. Execution results and
    // archive history are always loaded from their authenticated APIs.
    return {
      chronicles: [],
      subject: parsed.subject,
      pendingTask: parsed.pendingTask,
    };
  } catch {
    return EMPTY;
  }
}

export function writeProductSession(next: ProductSession) {
  sessionStorage.setItem(KEY, JSON.stringify({
    subject: next.subject,
    pendingTask: next.pendingTask,
  }));
  window.dispatchEvent(new CustomEvent("sanjiguan:session-change"));
}

export function updateProductSession(update: (current: ProductSession) => ProductSession) {
  writeProductSession(update(readProductSession()));
}

export function newId(prefix: string) {
  const random = crypto.getRandomValues(new Uint32Array(2));
  return `${prefix}-${Date.now().toString(36)}-${random[0].toString(36)}${random[1].toString(36)}`;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (init.method && init.method !== "GET" && !headers.has("Idempotency-Key")) {
    headers.set("Idempotency-Key", crypto.randomUUID());
  }
  const response = await fetch(path, { ...init, headers, credentials: "include" });
  if (!response.ok) {
    let message = "请求未完成";
    try {
      const body = await response.json();
      message = body?.error?.message || body?.detail || message;
    } catch {
      // Keep the user-safe fallback; never expose a raw stack.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}
