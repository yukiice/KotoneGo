/**
 * 极简 API 客户端：基于 fetch，统一错误处理。
 * 只依赖浏览器原生能力，方便替换成 axios / TanStack Query。
 */

import type {
  AnswerFeedback,
  CreateExamPayload,
  Exam,
  ExamDetail,
  ExamHistoryItem,
  ExamResult,
  Meta,
  Stats,
  WrongQuestion,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("无法连接后端服务，请确认 uvicorn 已启动（默认 8000 端口）", 0);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const data = text ? safeJson(text) : null;

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : `请求失败（${response.status}）`;
    throw new ApiError(detail, response.status);
  }
  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  meta: () => request<Meta>("/api/meta"),
  stats: () => request<Stats>("/api/stats"),

  createExam: (payload: CreateExamPayload) =>
    request<Exam>("/api/exams", { method: "POST", body: JSON.stringify(payload) }),
  getExamDetail: (id: string) => request<ExamDetail>(`/api/exams/${id}`),
  submitAnswer: (examId: string, questionId: string, selected: string) =>
    request<AnswerFeedback>(`/api/exams/${examId}/answers`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, selected }),
    }),
  finishExam: (examId: string) => request<ExamResult>(`/api/exams/${examId}/finish`, { method: "POST" }),
  listExams: (limit = 50) => request<ExamHistoryItem[]>(`/api/exams?limit=${limit}`),
  deleteExam: (id: string) => request<void>(`/api/exams/${id}`, { method: "DELETE" }),

  listWrongQuestions: (params?: { topic?: string; mastered?: boolean }) => {
    const search = new URLSearchParams();
    if (params?.topic) search.set("topic", params.topic);
    if (params?.mastered !== undefined) search.set("mastered", String(params.mastered));
    const qs = search.toString();
    return request<WrongQuestion[]>(`/api/wrong-questions${qs ? `?${qs}` : ""}`);
  },
  updateWrongQuestion: (questionId: string, payload: { mastered?: boolean; note?: string }) =>
    request<WrongQuestion>(`/api/wrong-questions/${questionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteWrongQuestion: (questionId: string) =>
    request<void>(`/api/wrong-questions/${questionId}`, { method: "DELETE" }),
};
