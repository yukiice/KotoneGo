import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { DOC_META } from "../content";
import { useAsync } from "../hooks/useAsync";
import { ErrorBox, Loading } from "../components/ui";

const SIZES = [5, 10, 20, 30];

export function HomePage() {
  const navigate = useNavigate();
  const meta = useAsync(() => api.meta(), []);
  const stats = useAsync(() => api.stats(), []);

  const [size, setSize] = useState(10);
  const [topics, setTopics] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<"any" | "easy" | "medium" | "hard">("any");
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastExamId = localStorage.getItem("kotone.lastExamId");

  async function startExam(onlyWrong = false) {
    setStarting(true);
    setError(null);
    try {
      const exam = await api.createExam({
        size,
        topics,
        difficulty,
        only_wrong: onlyWrong,
      });
      localStorage.setItem("kotone.lastExamId", exam.id);
      navigate(`/exam/${exam.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setStarting(false);
    }
  }

  function toggleTopic(topic: string) {
    setTopics((prev) => (prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]));
  }

  return (
    <div>
      <section className="hero">
        <h1>给前端开发者的 Python 语法课</h1>
        <p>
          你熟悉 React 与 TypeScript —— 这里用「对照迁移」的方式讲 Python：
          语法文档 18 章 + 随机抽题考试 + 错题本 + 学习统计，全部数据落库，可以长期跟踪进度。
        </p>
        <div className="row">
          <Link className="btn primary" to="/docs/01-hello-python">
            从第 1 章开始读
          </Link>
          <Link className="btn" to="/wrong">
            复习错题
          </Link>
          {lastExamId ? (
            <Link className="btn ghost" to={`/exam/${lastExamId}`}>
              继续上次考试
            </Link>
          ) : null}
        </div>
      </section>

      <section className="grid cols-4" style={{ margin: "22px 0" }}>
        <Stat label="题库总量" value={meta.data ? `${meta.data.question_count} 题` : "…"} />
        <Stat label="文档章节" value={`${DOC_META.length} 章`} />
        <Stat
          label="累计作答"
          value={stats.data ? `${stats.data.answered_questions} 题` : "…"}
        />
        <Stat
          label="待攻克错题"
          value={stats.data ? `${stats.data.wrong_open_count} 题` : "…"}
        />
      </section>

      <section className="grid cols-2" style={{ alignItems: "start" }}>
        <div className="card">
          <h2 style={{ fontSize: 18 }}>开始一场考试</h2>
          <p className="small muted" style={{ marginTop: -6 }}>
            每次随机抽题，满分 100 分（每题 10 分）。答完一题立即给出对错与解析，错题自动进错题本。
          </p>

          <div className="section-title small muted" style={{ marginTop: 14 }}>
            题量
          </div>
          <div className="row" style={{ margin: "6px 0 14px" }}>
            {SIZES.map((n) => (
              <button
                key={n}
                className={`topic-pill ${size === n ? "active" : ""}`}
                onClick={() => setSize(n)}
              >
                {n} 题
              </button>
            ))}
          </div>

          <div className="section-title small muted">难度</div>
          <div className="row" style={{ margin: "6px 0 14px" }}>
            {[
              { key: "any", label: "不限" },
              { key: "easy", label: "基础" },
              { key: "medium", label: "进阶" },
              { key: "hard", label: "较难" },
            ].map((item) => (
              <button
                key={item.key}
                className={`topic-pill ${difficulty === item.key ? "active" : ""}`}
                onClick={() => setDifficulty(item.key as typeof difficulty)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="section-title small muted">
            主题（不选 = 全部，已选 {topics.length} 个）
          </div>
          <div className="row" style={{ marginTop: 8 }}>
            {meta.loading ? <Loading text="加载主题…" /> : null}
            {meta.error ? <ErrorBox message={meta.error} onRetry={meta.reload} /> : null}
            {meta.data?.topics.map((topic) => (
              <button
                key={topic.topic}
                className={`topic-pill ${topics.includes(topic.topic) ? "active" : ""}`}
                onClick={() => toggleTopic(topic.topic)}
              >
                {topic.label}
                <span className="tiny muted"> {topic.count}</span>
              </button>
            ))}
          </div>

          {error ? (
            <div className="alert bad" style={{ marginTop: 14 }}>
              {error}
            </div>
          ) : null}

          <div className="row" style={{ marginTop: 18 }}>
            <button className="btn primary" onClick={() => void startExam(false)} disabled={starting}>
              {starting ? "正在抽题…" : "开始考试"}
            </button>
            <button
              className="btn ghost"
              onClick={() => void startExam(true)}
              disabled={starting}
              title="从错题本中未掌握的题目里抽题"
            >
              只练错题
            </button>
          </div>
        </div>

        <div className="card">
          <h2 style={{ fontSize: 18 }}>学习路线</h2>
          <p className="small muted" style={{ marginTop: -6 }}>
            建议顺序：先把「基础语法 → 数据类型 → 集合 → 函数」读通，再做题；每章末尾的自测清单可以直接对照。
          </p>
          <ol className="small" style={{ paddingLeft: 20, lineHeight: 1.9 }}>
            {DOC_META.slice(0, 9).map((doc) => (
              <li key={doc.slug}>
                <Link to={`/docs/${doc.slug}`}>{doc.title}</Link>
              </li>
            ))}
          </ol>
          <Link className="btn sm" to="/docs">
            查看全部 18 章
          </Link>

          {stats.data ? (
            <>
              <hr style={{ border: "none", borderTop: "1px solid var(--border)", margin: "18px 0" }} />
              <div className="row between">
                <span className="muted small">平均分</span>
                <strong>{stats.data.avg_score}</strong>
              </div>
              <div className="row between">
                <span className="muted small">最高分</span>
                <strong>{stats.data.best_score}</strong>
              </div>
              <div className="row between">
                <span className="muted small">考试次数</span>
                <strong>{stats.data.exam_count}</strong>
              </div>
            </>
          ) : null}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}
