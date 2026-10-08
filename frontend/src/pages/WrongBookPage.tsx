import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { WrongQuestion } from "../api/types";
import { Empty, ErrorBox, Loading, formatTime } from "../components/ui";
import { docTitle } from "../content";
import { useAsync } from "../hooks/useAsync";

type Filter = "open" | "mastered" | "all";

export function WrongBookPage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<Filter>("open");
  const [topic, setTopic] = useState<string>("");
  const [keyword, setKeyword] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const state = useAsync(
    () =>
      api.listWrongQuestions({
        mastered: filter === "all" ? undefined : filter === "mastered",
      }),
    [filter],
  );

  const items = state.data ?? [];

  const topics = useMemo(() => {
    const set = new Map<string, string>();
    items.forEach((item) => set.set(item.topic, item.topic_label));
    return [...set.entries()];
  }, [items]);

  const visible = items.filter((item) => {
    if (topic && item.topic !== topic) return false;
    if (keyword) {
      const q = keyword.toLowerCase();
      const hit =
        item.question.question.toLowerCase().includes(q) ||
        item.explanation.toLowerCase().includes(q) ||
        item.topic_label.includes(keyword);
      if (!hit) return false;
    }
    return true;
  });

  async function toggleMastered(item: WrongQuestion) {
    setBusy(item.question_id);
    try {
      await api.updateWrongQuestion(item.question_id, { mastered: !item.mastered });
      await state.reload();
    } finally {
      setBusy(null);
    }
  }

  async function saveNote(item: WrongQuestion, note: string) {
    setBusy(item.question_id);
    try {
      await api.updateWrongQuestion(item.question_id, { note });
      await state.reload();
    } finally {
      setBusy(null);
    }
  }

  async function remove(item: WrongQuestion) {
    if (!confirm("从错题本移除这道题？（历史统计仍会保留）")) return;
    setBusy(item.question_id);
    try {
      await api.deleteWrongQuestion(item.question_id);
      await state.reload();
    } finally {
      setBusy(null);
    }
  }

  async function practiceWrong() {
    const exam = await api.createExam({ size: 10, only_wrong: true });
    localStorage.setItem("kotone.lastExamId", exam.id);
    navigate(`/exam/${exam.id}`);
  }

  if (state.loading) return <Loading text="加载错题本…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;

  return (
    <div>
      <div className="row between" style={{ marginBottom: 14 }}>
        <div>
          <h1 style={{ fontSize: 22, marginBottom: 4 }}>错题本</h1>
          <p className="small muted" style={{ margin: 0 }}>
            每道错题都记录了错误次数、最近一次的错误选项与时间，方便你按薄弱点复习。
          </p>
        </div>
        <div className="row">
          <button className="btn primary sm" onClick={() => void practiceWrong()}>
            只练错题
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row">
          {(
            [
              { key: "open", label: "待攻克" },
              { key: "mastered", label: "已掌握" },
              { key: "all", label: "全部" },
            ] as const
          ).map((item) => (
            <button
              key={item.key}
              className={`topic-pill ${filter === item.key ? "active" : ""}`}
              onClick={() => setFilter(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="grid cols-2" style={{ marginTop: 12 }}>
          <div>
            <div className="tiny muted">按主题筛选</div>
            <select value={topic} onChange={(event) => setTopic(event.target.value)}>
              <option value="">全部主题</option>
              {topics.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="tiny muted">关键词</div>
            <input
              type="search"
              placeholder="搜索题干 / 解析"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
        </div>
      </div>

      {visible.length === 0 ? (
        <Empty
          text={
            filter === "open"
              ? "太棒了，没有待攻克的错题。"
              : "这个筛选条件下没有错题记录。"
          }
          action={
            <Link className="btn" to="/exam">
              去做一场考试
            </Link>
          }
        />
      ) : (
        <div className="grid" style={{ gap: 14 }}>
          {visible.map((item) => (
            <WrongItem
              key={item.question_id}
              item={item}
              busy={busy === item.question_id}
              onToggle={() => void toggleMastered(item)}
              onRemove={() => void remove(item)}
              onSaveNote={(note) => void saveNote(item, note)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function WrongItem({
  item,
  busy,
  onToggle,
  onRemove,
  onSaveNote,
}: {
  item: WrongQuestion;
  busy: boolean;
  onToggle: () => void;
  onRemove: () => void;
  onSaveNote: (note: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState(item.note);

  return (
    <div className={`wrong-item ${item.mastered ? "mastered" : ""}`}>
      <div className="row between" style={{ marginBottom: 8 }}>
        <div className="row" style={{ gap: 6 }}>
          <span className="chip brand">{item.topic_label}</span>
          <span className="chip bad">错 {item.wrong_count} 次</span>
          {item.mastered ? <span className="chip ok">已掌握</span> : null}
        </div>
        <span className="tiny muted">最近错误：{formatTime(item.last_wrong_at)}</span>
      </div>

      <p className="wrong-q">{item.question.question}</p>

      <div className="row between" style={{ marginTop: 10 }}>
        <div className="row tiny">
          <span className="chip bad">你选了 {item.last_selected ?? "—"}</span>
          <span className="chip ok">正确答案 {item.correct_answer}</span>
        </div>
        <div className="row">
          <button className="btn sm ghost" onClick={() => setOpen((prev) => !prev)}>
            {open ? "收起解析" : "查看解析"}
          </button>
          <button className="btn sm" disabled={busy} onClick={onToggle}>
            {item.mastered ? "重新标记待攻克" : "标记已掌握"}
          </button>
          <button className="btn sm danger" disabled={busy} onClick={onRemove}>
            移除
          </button>
        </div>
      </div>

      {open ? (
        <div className="feedback bad" style={{ marginTop: 12 }}>
          <div className="section">
            <div className="section-title">选项</div>
            <div className="grid" style={{ gap: 6 }}>
              {Object.entries(item.question.options).map(([key, text]) => (
                <div key={key} className="small">
                  <span
                    className="chip"
                    style={{
                      borderColor:
                        key === item.correct_answer
                          ? "var(--ok)"
                          : key === item.last_selected
                            ? "var(--bad)"
                            : undefined,
                      color:
                        key === item.correct_answer
                          ? "var(--ok)"
                          : key === item.last_selected
                            ? "var(--bad)"
                            : undefined,
                    }}
                  >
                    {key}
                  </span>{" "}
                  {text}
                </div>
              ))}
            </div>
          </div>

          <div className="section">
            <div className="section-title">正确答案为什么是 {item.correct_answer}</div>
            <p style={{ margin: 0 }}>{item.explanation}</p>
          </div>

          {item.why_wrong ? (
            <div className="section">
              <div className="section-title">我为什么选错（{item.last_selected}）</div>
              <p style={{ margin: 0 }}>{item.why_wrong}</p>
            </div>
          ) : null}

          {item.knowledge.length > 0 ? (
            <div className="section">
              <div className="section-title">相关知识点</div>
              <div className="row">
                {item.knowledge.map((k) => (
                  <span className="chip" key={k}>
                    {k}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {item.doc ? (
            <div className="section">
              <div className="section-title">对应文档</div>
              <Link to={`/docs/${item.doc}`}>📖 {docTitle(item.doc)}</Link>
            </div>
          ) : null}

          <div className="section">
            <div className="section-title">我的笔记（保存到数据库）</div>
            <textarea
              className="note-input"
              rows={3}
              value={note}
              placeholder="例如：记住 // 是向下取整，负数要小心"
              onChange={(event) => setNote(event.target.value)}
            />
            <div style={{ marginTop: 8 }}>
              <button className="btn sm" disabled={busy} onClick={() => onSaveNote(note)}>
                保存笔记
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
