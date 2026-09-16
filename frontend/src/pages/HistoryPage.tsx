import { Link } from "react-router-dom";
import { useState } from "react";
import { api } from "../api/client";
import { Empty, ErrorBox, Loading, formatDuration, formatTime } from "../components/ui";
import { useAsync } from "../hooks/useAsync";

export function HistoryPage() {
  const state = useAsync(() => api.listExams(100), []);
  const [removing, setRemoving] = useState<string | null>(null);

  async function remove(id: string) {
    if (!confirm("删除这场考试记录？该操作不可撤销。")) return;
    setRemoving(id);
    try {
      await api.deleteExam(id);
      await state.reload();
    } finally {
      setRemoving(null);
    }
  }

  if (state.loading) return <Loading text="加载考试记录…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;

  const exams = state.data ?? [];

  return (
    <div>
      <div className="row between" style={{ marginBottom: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, marginBottom: 4 }}>考试记录</h1>
          <p className="small muted" style={{ margin: 0 }}>
            共 {exams.length} 场。数据保存在后端 SQLite（backend/data/kotone.db），可以直接查询分析。
          </p>
        </div>
        <Link className="btn primary sm" to="/exam">
          开始新考试
        </Link>
      </div>

      {exams.length === 0 ? (
        <Empty
          text="还没有考试记录，先来一场随机测试吧。"
          action={
            <Link className="btn primary" to="/exam">
              开始考试
            </Link>
          }
        />
      ) : (
        <div className="grid" style={{ gap: 12 }}>
          {exams.map((exam) => (
            <div className="card" key={exam.id}>
              <div className="row between">
                <div className="row" style={{ gap: 8 }}>
                  <span className={`chip ${exam.status === "finished" ? "brand" : "warn"}`}>
                    {exam.status === "finished" ? "已交卷" : "进行中"}
                  </span>
                  <strong style={{ fontSize: 20 }}>{exam.score}</strong>
                  <span className="tiny muted">分</span>
                  <span className="chip">
                    {exam.correct_count}/{exam.size} 正确
                  </span>
                </div>
                <span className="spacer" />
                <div className="row">
                  <Link className="btn sm" to={exam.status === "finished" ? `/result/${exam.id}` : `/exam/${exam.id}`}>
                    {exam.status === "finished" ? "查看解析" : "继续作答"}
                  </Link>
                  <button
                    className="btn sm danger"
                    onClick={() => void remove(exam.id)}
                    disabled={removing === exam.id}
                  >
                    删除
                  </button>
                </div>
              </div>
              <div className="tiny muted" style={{ marginTop: 8 }}>
                开始 {formatTime(exam.created_at)} · 用时 {formatDuration(exam.duration_seconds)} · 题量{" "}
                {exam.size}
                {exam.topics.length > 0 ? ` · 主题：${exam.topics.join("、")}` : " · 全主题随机"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
