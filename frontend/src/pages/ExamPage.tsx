import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { AnswerFeedback, ExamDetail, ExamQuestion } from "../api/types";
import { QuestionCard, type FeedbackLike } from "../components/QuestionCard";
import { ErrorBox, Loading, ScoreRing, formatDuration } from "../components/ui";
import { useAsync } from "../hooks/useAsync";

/** ---------------- 考试设置页 /exam ---------------- */
export function ExamSetupPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const presetTopic = params.get("topic");
  const meta = useAsync(() => api.meta(), []);
  const [size, setSize] = useState(10);
  const [topics, setTopics] = useState<string[]>(presetTopic ? [presetTopic] : []);
  const [difficulty, setDifficulty] = useState<"any" | "easy" | "medium" | "hard">("any");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (presetTopic) setTopics([presetTopic]);
  }, [presetTopic]);

  async function start(onlyWrong = false) {
    setStarting(true);
    setError(null);
    try {
      const exam = await api.createExam({ size, topics, difficulty, only_wrong: onlyWrong });
      localStorage.setItem("kotone.lastExamId", exam.id);
      navigate(`/exam/${exam.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="grid cols-2" style={{ alignItems: "start" }}>
      <div className="card">
        <h1 style={{ fontSize: 22 }}>开始一场考试</h1>
        <p className="small muted">
          默认 10 题（每题 10 分，满分 100）。每题作答后立刻显示对错与理由，全部答完显示成绩。
        </p>

        <div className="section-title tiny muted">题量</div>
        <div className="row" style={{ margin: "6px 0 14px" }}>
          {[5, 10, 20, 30, 50].map((n) => (
            <button key={n} className={`topic-pill ${size === n ? "active" : ""}`} onClick={() => setSize(n)}>
              {n} 题
            </button>
          ))}
        </div>

        <div className="section-title tiny muted">难度</div>
        <div className="row" style={{ margin: "6px 0 14px" }}>
          {(["any", "easy", "medium", "hard"] as const).map((key) => (
            <button
              key={key}
              className={`topic-pill ${difficulty === key ? "active" : ""}`}
              onClick={() => setDifficulty(key)}
            >
              {{ any: "不限", easy: "基础", medium: "进阶", hard: "较难" }[key]}
            </button>
          ))}
        </div>

        <div className="section-title tiny muted">主题（不选 = 全部）</div>
        <div className="row" style={{ marginTop: 8 }}>
          {meta.data?.topics.map((topic) => (
            <button
              key={topic.topic}
              className={`topic-pill ${topics.includes(topic.topic) ? "active" : ""}`}
              onClick={() =>
                setTopics((prev) =>
                  prev.includes(topic.topic) ? prev.filter((t) => t !== topic.topic) : [...prev, topic.topic],
                )
              }
            >
              {topic.label} <span className="tiny muted">{topic.count}</span>
            </button>
          ))}
        </div>

        {error ? (
          <div className="alert bad" style={{ marginTop: 14 }}>
            {error}
          </div>
        ) : null}

        <div className="row" style={{ marginTop: 18 }}>
          <button className="btn primary" disabled={starting} onClick={() => void start(false)}>
            {starting ? "抽题中…" : "开始考试"}
          </button>
          <button className="btn ghost" disabled={starting} onClick={() => void start(true)}>
            只练错题
          </button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ fontSize: 18 }}>考试规则</h2>
        <ul className="small" style={{ paddingLeft: 20, lineHeight: 1.9 }}>
          <li>每次进入随机抽题，题目不重复。</li>
          <li>答错立刻显示正确答案、错因与相关知识点，并自动进入错题本。</li>
          <li>可以「下一题」跳过，未作答的题目会在交卷时按 0 分计算。</li>
          <li>同一场考试重复作答同一题会覆盖上一次结果。</li>
          <li>中途刷新或关闭页面不会丢进度（服务端保存）。</li>
          <li>每场考试都会记录分数、用时与各主题正确率。</li>
        </ul>
        <p className="small muted">
          小提示：错题在后续考试中答对一次就会标记为「已掌握」，但错误次数会一直保留，方便你追溯薄弱点。
        </p>
      </div>
    </div>
  );
}

/** ---------------- 考试进行页 /exam/:examId ---------------- */
export function ExamRunnerPage() {
  const { examId = "" } = useParams();
  const navigate = useNavigate();
  const state = useAsync<ExamDetail>(() => api.getExamDetail(examId), [examId]);

  const [index, setIndex] = useState(0);
  const [feedback, setFeedback] = useState<Record<string, FeedbackLike>>({});
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initialized = useRef<string | null>(null);

  // 首次加载：把服务端已作答的记录还原成反馈面板
  useEffect(() => {
    const detail = state.data;
    if (!detail || initialized.current === detail.exam.id) return;
    initialized.current = detail.exam.id;

    const restored: Record<string, FeedbackLike> = {};
    detail.answers.forEach((answer) => {
      if (answer.selected) {
        restored[answer.question.id] = {
          selected: answer.selected,
          is_correct: answer.is_correct,
          correct_answer: answer.correct_answer,
          explanation: answer.explanation,
          why_wrong: answer.why_wrong,
          knowledge: answer.knowledge,
          doc: answer.doc,
        };
      }
    });
    setFeedback(restored);

    const questionIds = detail.answers.map((a) => a.question.id);
    const unansweredIndex = questionIds.findIndex((id) => !restored[id]);
    setIndex(unansweredIndex === -1 ? Math.max(0, questionIds.length - 1) : unansweredIndex);
  }, [state.data]);

  const detail = state.data;
  const questions: ExamQuestion[] = useMemo(
    () => detail?.answers.map((a) => a.question) ?? [],
    [detail],
  );

  const current = questions[index];
  const currentFeedback = current ? feedback[current.id] ?? null : null;
  const answeredCount = Object.keys(feedback).length;
  const correctCount = Object.values(feedback).filter((item) => item.is_correct).length;

  const select = useCallback(
    async (key: string) => {
      if (!current || currentFeedback || submitting) return;
      setSubmitting(true);
      setError(null);
      try {
        const result: AnswerFeedback = await api.submitAnswer(examId, current.id, key);
        setFeedback((prev) => ({
          ...prev,
          [current.id]: {
            selected: result.selected,
            is_correct: result.is_correct,
            correct_answer: result.correct_answer,
            explanation: result.explanation,
            why_wrong: result.why_wrong,
            knowledge: result.knowledge,
            doc: result.doc,
          },
        }));
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setSubmitting(false);
      }
    },
    [current, currentFeedback, examId, submitting],
  );

  const finish = useCallback(async () => {
    setFinishing(true);
    setError(null);
    try {
      await api.finishExam(examId);
      navigate(`/result/${examId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setFinishing(false);
    }
  }, [examId, navigate]);

  const next = useCallback(() => {
    if (index < questions.length - 1) {
      setIndex((prev) => prev + 1);
    } else {
      void finish();
    }
  }, [finish, index, questions.length]);

  // 桌面端键盘操作：1-4 选项，Enter/→ 下一题
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (!current) return;
      const keys = Object.keys(current.options);
      const num = Number(event.key);
      if (num >= 1 && num <= keys.length) {
        const key = keys[num - 1];
        if (key) void select(key);
        return;
      }
      if ((event.key === "Enter" || event.key === "ArrowRight") && currentFeedback) {
        event.preventDefault();
        next();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [current, currentFeedback, next, select]);

  if (state.loading) return <Loading text="正在加载考卷…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;
  if (!detail || !current) {
    return (
      <div className="empty">
        这场考试没有题目（题库可能已变化）。
        <div style={{ marginTop: 12 }}>
          <Link className="btn" to="/exam">
            重新开始
          </Link>
        </div>
      </div>
    );
  }

  const isFinished = detail.exam.status === "finished";

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="exam-head">
        <span className="chip brand">考试 {detail.exam.id.slice(0, 6)}</span>
        <span className="chip">{detail.exam.size} 题</span>
        <span className="chip">
          已答 {answeredCount} / {questions.length}
        </span>
        <span className="chip ok">正确 {correctCount}</span>
        <span className="chip warn">
          当前得分 {Math.round((correctCount / questions.length) * 100) || 0}
        </span>
        <span className="spacer" />
        <Link className="btn sm ghost" to="/history">
          退出（进度已保存）
        </Link>
      </div>

      <div className="progress">
        <span style={{ width: `${(answeredCount / questions.length) * 100}%` }} />
      </div>

      {isFinished ? (
        <div className="alert ok">
          这场考试已经交卷。<Link to={`/result/${examId}`}>查看结果与解析 →</Link>
        </div>
      ) : null}

      <QuestionCard
        question={current}
        index={index}
        total={questions.length}
        selected={currentFeedback?.selected ?? null}
        feedback={currentFeedback}
        onSelect={(key) => void select(key)}
      />

      {error ? <div className="alert bad">{error}</div> : null}

      <div className="row between">
        <button className="btn" disabled={index === 0} onClick={() => setIndex((prev) => prev - 1)}>
          ← 上一题
        </button>
        <span className="tiny muted">
          {currentFeedback
            ? "已作答，可以继续下一题"
            : "选择答案后会立即给出解析"}
        </span>
        <button
          className="btn primary"
          onClick={next}
          disabled={finishing || submitting}
        >
          {finishing
            ? "交卷中…"
            : index === questions.length - 1
              ? "交卷并查看成绩"
              : "下一题 →"}
        </button>
      </div>

      <div className="card">
        <div className="row between" style={{ marginBottom: 8 }}>
          <strong className="small">题目导航</strong>
          <span className="tiny muted">灰色 = 未作答</span>
        </div>
        <div className="row">
          {questions.map((question, i) => {
            const item = feedback[question.id];
            return (
              <button
                key={question.id}
                className="topic-pill"
                style={{
                  minWidth: 46,
                  justifyContent: "center",
                  borderColor: item ? (item.is_correct ? "var(--ok)" : "var(--bad)") : undefined,
                  color: item ? (item.is_correct ? "var(--ok)" : "var(--bad)") : undefined,
                  background: item
                    ? item.is_correct
                      ? "var(--ok-soft)"
                      : "var(--bad-soft)"
                    : undefined,
                }}
                onClick={() => setIndex(i)}
              >
                {i + 1}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export function ExamResultPage() {
  const { examId = "" } = useParams();
  const navigate = useNavigate();
  const state = useAsync<ExamDetail>(() => api.getExamDetail(examId), [examId]);

  if (state.loading) return <Loading text="正在加载成绩…" />;
  if (state.error) return <ErrorBox message={state.error} onRetry={state.reload} />;
  if (!state.data) return null;

  const { exam, answers } = state.data;

  async function repeat() {
    const created = await api.createExam({
      size: exam.size,
      topics: exam.by_topic.map((item) => item.topic),
    });
    localStorage.setItem("kotone.lastExamId", created.id);
    navigate(`/exam/${created.id}`);
  }

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card">
        <div className="row" style={{ gap: 20 }}>
          <ScoreRing score={exam.score} />
          <div>
            <h1 style={{ fontSize: 22, marginBottom: 6 }}>
              {exam.score >= 90 ? "非常棒！" : exam.score >= 70 ? "不错，继续巩固" : "还有提升空间"}
            </h1>
            <p className="small muted" style={{ margin: 0 }}>
              共 {exam.size} 题 · 正确 {exam.correct_count} 题 · 错误 {exam.wrong_count} 题
              <br />
              用时 {formatDuration(exam.duration_seconds)} · 交卷时间 {exam.finished_at ?? "未交卷"}
            </p>
            <div className="row" style={{ marginTop: 12 }}>
              <button className="btn primary sm" onClick={() => void repeat()}>
                同范围再来一场
              </button>
              <Link className="btn sm" to="/wrong">
                查看错题本
              </Link>
              <Link className="btn sm ghost" to="/history">
                考试记录
              </Link>
            </div>
          </div>
        </div>

        {exam.by_topic.length > 0 ? (
          <div style={{ marginTop: 18 }}>
            <div className="section-title tiny muted">各主题正确率</div>
            <div className="grid" style={{ gap: 10 }}>
              {exam.by_topic.map((topic) => {
                const pct = topic.total ? Math.round((topic.correct / topic.total) * 100) : 0;
                return (
                  <div key={topic.topic}>
                    <div className="row between tiny">
                      <span>{topic.label}</span>
                      <span className="muted">
                        {topic.correct}/{topic.total}（{pct}%）
                      </span>
                    </div>
                    <div className="bar">
                      <span style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>

      <h2 style={{ fontSize: 18, marginBottom: 0 }}>逐题解析</h2>
      {answers.map((answer, i) => (
        <QuestionCard
          key={answer.question.id}
          question={answer.question}
          index={i}
          total={answers.length}
          selected={answer.selected}
          feedback={
            answer.selected
              ? {
                  selected: answer.selected,
                  is_correct: answer.is_correct,
                  correct_answer: answer.correct_answer,
                  explanation: answer.explanation,
                  why_wrong: answer.why_wrong,
                  knowledge: answer.knowledge,
                  doc: answer.doc,
                }
              : {
                  selected: "",
                  is_correct: false,
                  correct_answer: answer.correct_answer,
                  explanation: answer.explanation,
                  why_wrong: "这道题你当时没有作答。",
                  knowledge: answer.knowledge,
                  doc: answer.doc,
                }
          }
          onSelect={() => undefined}
        />
      ))}
    </div>
  );
}
