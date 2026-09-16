import { Link } from "react-router-dom";
import { api } from "../api/client";
import { ErrorBox, Loading, ScoreRing, formatDuration, formatTime } from "../components/ui";
import { useAsync } from "../hooks/useAsync";

export function StatsPage() {
  const state = useAsync(() => api.stats(), []);

  if (state.loading) return <Loading text="加载统计…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;
  if (!state.data) return null;

  const stats = state.data;
  const weakest = [...stats.by_topic]
    .filter((item) => item.attempts > 0)
    .sort((a, b) => a.accuracy - b.accuracy)
    .slice(0, 3);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="row between">
        <div>
          <h1 style={{ fontSize: 22, marginBottom: 4 }}>学习统计</h1>
          <p className="small muted" style={{ margin: 0 }}>
            数据来自 backend/data/kotone.db，可以随时用 SQL 或脚本做进一步分析。
          </p>
        </div>
        <Link className="btn primary sm" to="/exam">
          再来一场
        </Link>
      </div>

      <div className="grid cols-4">
        <StatCard label="考试次数" value={String(stats.exam_count)} hint={`已交卷 ${stats.finished_exam_count} 场`} />
        <StatCard label="累计作答" value={`${stats.answered_questions} 题`} hint={`题库共 ${stats.bank_size} 题`} />
        <StatCard label="平均分 / 最高分" value={`${stats.avg_score} / ${stats.best_score}`} hint="满分 100" />
        <StatCard
          label="待攻克错题"
          value={String(stats.wrong_open_count)}
          hint={`已掌握 ${stats.wrong_mastered_count} 题`}
        />
      </div>

      <div className="card">
        <div className="row" style={{ gap: 24 }}>
          <ScoreRing score={Math.round(stats.avg_score)} />
          <div>
            <h2 style={{ fontSize: 18, marginBottom: 6 }}>总体表现</h2>
            <p className="small muted" style={{ margin: 0 }}>
              累计学习时长 {stats.total_minutes} 分钟。
              <br />
              建议优先攻克正确率最低的主题，然后回到错题本做「只练错题」。
            </p>
            {weakest.length > 0 ? (
              <div className="row" style={{ marginTop: 12 }}>
                <span className="tiny muted">最薄弱：</span>
                {weakest.map((item) => (
                  <span className="chip bad" key={item.topic}>
                    {item.label} {item.accuracy}%
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ fontSize: 18 }}>各主题正确率</h2>
        <div className="grid" style={{ gap: 12 }}>
          {stats.by_topic.map((item) => (
            <div key={item.topic}>
              <div className="row between tiny">
                <span>
                  {item.label} <span className="muted">（题库 {item.bank_count} 题）</span>
                </span>
                <span className="muted">
                  {item.attempts === 0
                    ? "尚未练习"
                    : `${item.correct}/${item.attempts} = ${item.accuracy}%`}
                  {item.wrong_open > 0 ? ` · 待攻克 ${item.wrong_open}` : ""}
                </span>
              </div>
              <div className="bar">
                <span style={{ width: `${item.accuracy}%` }} />
              </div>
              <div className="row" style={{ marginTop: 6 }}>
                <Link className="btn sm ghost" to={`/exam?topic=${item.topic}`}>
                  练这个主题
                </Link>
                <Link className="btn sm ghost" to={`/docs`}>
                  查文档
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 style={{ fontSize: 18 }}>最近考试</h2>
        {stats.recent_exams.length === 0 ? (
          <p className="muted small">还没有考试记录。</p>
        ) : (
          <div className="grid" style={{ gap: 8 }}>
            {stats.recent_exams.map((exam) => (
              <div className="row between" key={exam.id}>
                <div className="row small">
                  <strong>{exam.score}</strong>
                  <span className="muted">分</span>
                  <span className="chip">{exam.correct_count}/{exam.size}</span>
                  <span className="tiny muted">{formatTime(exam.created_at)}</span>
                  <span className="tiny muted">用时 {formatDuration(exam.duration_seconds)}</span>
                </div>
                <Link
                  className="btn sm"
                  to={exam.status === "finished" ? `/result/${exam.id}` : `/exam/${exam.id}`}
                >
                  {exam.status === "finished" ? "解析" : "继续"}
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="stat">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="tiny muted">{hint}</div> : null}
    </div>
  );
}
