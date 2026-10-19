import { useState } from "react";
import { api } from "../api/client";
import type { QuestionReport } from "../api/types";
import { Empty, ErrorBox, Loading, formatTime } from "../components/ui";
import { useAsync } from "../hooks/useAsync";

type Filter = "open" | "resolved" | "all";

const FILTERS: { key: Filter; label: string }[] = [
  { key: "open", label: "待处理" },
  { key: "resolved", label: "已修复" },
  { key: "all", label: "全部" },
];

/**
 * 题目反馈处理页：查看学习者的「这题有问题」上报，并标记已修复或重新打开。
 * 只改上报状态，不会自动修改题库；题库修订仍需手动编辑 JSON 并校验。
 */
export function ReportsPage() {
  const [filter, setFilter] = useState<Filter>("open");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const state = useAsync(
    () => api.listQuestionReports(filter === "all" ? undefined : filter),
    [filter],
  );
  const items = state.data ?? [];

  async function setStatus(report: QuestionReport, status: "open" | "resolved") {
    setBusyId(report.id);
    setActionError(null);
    try {
      await api.updateQuestionReport(report.id, status);
      await state.reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "操作失败，请稍后再试");
    } finally {
      setBusyId(null);
    }
  }

  if (state.loading) return <Loading text="加载反馈…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <h1 style={{ fontSize: 22, marginBottom: 4 }}>题目反馈</h1>
        <p className="small muted" style={{ margin: 0 }}>
          学习者在答题或错题本里报告的题目问题。处理后标记为已修复；修改题库需要另外编辑题目文件。
        </p>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row">
          {FILTERS.map((item) => (
            <button
              key={item.key}
              className={`topic-pill ${filter === item.key ? "active" : ""}`}
              onClick={() => setFilter(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {actionError ? <div className="alert bad" style={{ marginBottom: 14 }}>{actionError}</div> : null}

      {items.length === 0 ? (
        <Empty text={filter === "resolved" ? "还没有标记为已修复的反馈。" : "目前没有待处理的反馈。"} />
      ) : (
        <div className="grid" style={{ gap: 14 }}>
          {items.map((item) => (
            <div key={item.id} className={`wrong-item ${item.status === "resolved" ? "mastered" : ""}`}>
              <div className="row between" style={{ marginBottom: 8 }}>
                <div className="row" style={{ gap: 6 }}>
                  <span className="chip brand">{item.category_label}</span>
                  <span className={`chip ${item.status === "resolved" ? "ok" : "bad"}`}>
                    {item.status === "resolved" ? "已修复" : "待处理"}
                  </span>
                  <span className="tiny muted">题号 {item.question_id}</span>
                </div>
                <span className="tiny muted">{formatTime(item.created_at)}</span>
              </div>

              <p className="wrong-q">{item.question}</p>

              {item.message ? (
                <div className="feedback" style={{ marginTop: 8 }}>
                  <div className="section-title">补充说明</div>
                  <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{item.message}</p>
                </div>
              ) : (
                <p className="tiny muted" style={{ margin: "8px 0 0" }}>
                  未填写补充说明。
                </p>
              )}

              <div className="row" style={{ justifyContent: "flex-end", marginTop: 12 }}>
                {item.status === "open" ? (
                  <button
                    className="btn sm primary"
                    disabled={busyId === item.id}
                    onClick={() => void setStatus(item, "resolved")}
                  >
                    标记已修复
                  </button>
                ) : (
                  <button
                    className="btn sm"
                    disabled={busyId === item.id}
                    onClick={() => void setStatus(item, "open")}
                  >
                    重新打开
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
