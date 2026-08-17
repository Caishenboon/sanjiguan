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

export function friendlyErrorMessage(value: unknown) {
  const raw = value instanceof Error ? value.message : String(value || "");
  if (/api_origin_not_configured|failed to fetch|networkerror|load failed/i.test(raw)) {
    return "暂时无法连接三际观服务。你的未提交内容仍保留在本页，请稍后重试。";
  }
  if (/authentication_required|unauthorized|401/i.test(raw)) {
    return "当前会话已失效，请重新进入私人空间后继续。";
  }
  if (/forbidden|permission|403/i.test(raw)) {
    return "当前账号没有执行此操作的授权。请返回上一页或联系所有者。";
  }
  if (/not_found|404/i.test(raw)) {
    return "未找到可读取的内容，或当前账号无权确认它是否存在。";
  }
  const isShortUserCopy = raw.length <= 160 && /[\u3400-\u9fff]/.test(raw) && !/(traceback|stack|exception|sql|database|fetch|http\b|error\b)/i.test(raw);
  return isShortUserCopy ? raw : "请求暂未完成。你的资料没有被覆盖，可以稍后重试。";
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
      message = friendlyErrorMessage(body?.error?.message || body?.detail || message);
    } catch {
      // Keep the user-safe fallback; never expose a raw stack.
    }
    throw new Error(friendlyErrorMessage(message));
  }
  return response.json() as Promise<T>;
}
