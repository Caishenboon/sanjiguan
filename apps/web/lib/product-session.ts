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
  if (/request_timeout|timeout|aborted/i.test(raw)) {
    return "连接等待时间过长。你的未提交内容仍保留在本页，可以立即重试。";
  }
  if (/api_origin_not_configured|failed to fetch|networkerror|load failed/i.test(raw)) {
    return "暂时无法连接三际观服务。你的未提交内容仍保留在本页，请稍后重试。";
  }
  if (/authentication_required|unauthorized|401/i.test(raw)) {
    return "当前会话已失效，请重新进入私人空间后继续。";
  }
  if (/bootstrap_unavailable|owner_already_initialized/i.test(raw)) {
    return "初始化口令无效，或本地所有者已经建立。";
  }
  if (/invalid_or_expired_invitation/i.test(raw)) {
    return "邀请已失效、已使用或输入不完整，请向所有者申请新的邀请。";
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

export class ProductApiError extends Error {
  constructor(
    message: string,
    readonly requestId?: string,
    readonly status?: number,
  ) {
    super(requestId ? `${message} 关联ID：${requestId}` : message);
    this.name = "ProductApiError";
  }
}

export type ApiRequestInit = RequestInit & { timeoutMs?: number };

export async function apiRequest<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { timeoutMs = 15_000, signal: upstreamSignal, ...requestInit } = init;
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (init.method && init.method !== "GET" && !headers.has("Idempotency-Key")) {
    headers.set("Idempotency-Key", crypto.randomUUID());
  }
  if (!headers.has("X-Request-ID")) headers.set("X-Request-ID", crypto.randomUUID());
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort(upstreamSignal?.reason);
  upstreamSignal?.addEventListener("abort", abortFromCaller, { once: true });
  const timeout = window.setTimeout(() => controller.abort("request_timeout"), timeoutMs);
  let response: Response;
  try {
    response = await fetch(path, {
      ...requestInit,
      headers,
      credentials: "include",
      cache: "no-store",
      signal: controller.signal,
    });
  } catch (error) {
    const message = controller.signal.aborted && !upstreamSignal?.aborted
      ? friendlyErrorMessage("request_timeout")
      : friendlyErrorMessage(error);
    throw new ProductApiError(message, headers.get("X-Request-ID") || undefined);
  } finally {
    window.clearTimeout(timeout);
    upstreamSignal?.removeEventListener("abort", abortFromCaller);
  }
  const requestId = response.headers.get("X-Request-ID") || headers.get("X-Request-ID") || undefined;
  if (!response.ok) {
    let message = "请求未完成";
    try {
      const body = await response.json();
      message = friendlyErrorMessage(body?.error?.message || body?.detail || message);
    } catch {
      // Keep the user-safe fallback; never expose a raw stack.
    }
    throw new ProductApiError(friendlyErrorMessage(message), requestId, response.status);
  }
  return response.json() as Promise<T>;
}
