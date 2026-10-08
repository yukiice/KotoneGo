import { Link } from "react-router-dom";
import type { ExamQuestion } from "../api/types";
import { docTitle } from "../content";

/** 与后端 AnswerFeedback / AnswerDetail 兼容的最小结构 */
export interface FeedbackLike {
  selected: string;
  is_correct: boolean | null;
  correct_answer: string;
  explanation: string;
  why_wrong: string | null;
  knowledge: string[];
  doc: string;
}

const OPTION_KEYS = ["A", "B", "C", "D", "E", "F"];

export function QuestionCard({
  question,
  index,
  total,
  selected,
  feedback,
  onSelect,
}: {
  question: ExamQuestion;
  index: number;
  total: number;
  selected: string | null;
  feedback: FeedbackLike | null;
  onSelect: (key: string) => void;
}) {
  const answered = Boolean(feedback);
  const isCorrect = feedback?.is_correct ?? null;
  const keys = Object.keys(question.options);

  return (
    <div className="card fade-in">
      <div className="row between" style={{ marginBottom: 12 }}>
        <span className="chip brand">{question.topic_label}</span>
        <span className="tiny muted">
          第 {index + 1} / {total} 题 · {difficultyLabel(question.difficulty)}
        </span>
      </div>

      <p className="question-text">{question.question}</p>

      <div className="grid" style={{ marginTop: 16 }}>
        {keys.map((key) => {
          const state = optionState(key, selected, feedback);
          return (
            <button
              key={key}
              className={`option ${state}`}
              onClick={() => onSelect(key)}
              disabled={answered}
              aria-pressed={selected === key}
            >
              <span className="key">{key}</span>
              <span>{question.options[key]}</span>
              {state === "correct" ? <span className="chip ok">正确答案</span> : null}
              {state === "wrong" ? <span className="chip bad">你的选择</span> : null}
            </button>
          );
        })}
      </div>

      {feedback ? (
        <div className={`feedback fade-in ${isCorrect ? "ok" : "bad"}`}>
          <h3>
            {isCorrect ? "✅ 答对了" : "❌ 答错了"}
            {!isCorrect ? (
              <span className="chip bad" style={{ marginLeft: 6 }}>
                正确答案：{feedback.correct_answer}
              </span>
            ) : null}
          </h3>

          <div className="section">
            <div className="section-title">为什么是这个答案</div>
            <p style={{ margin: 0 }}>{feedback.explanation}</p>
          </div>

          {!isCorrect && feedback.why_wrong ? (
            <div className="section">
              <div className="section-title">
                你选的 {feedback.selected} 为什么不对
              </div>
              <p style={{ margin: 0 }}>{feedback.why_wrong}</p>
            </div>
          ) : null}

          {!isCorrect && !feedback.why_wrong ? (
            <div className="section">
              <div className="section-title">提示</div>
              <p className="muted" style={{ margin: 0 }}>
                这道题还没有为选项 {feedback.selected} 写专门的错因说明，
                对照上面的解析理解差异，并回到对应文档复习。
              </p>
            </div>
          ) : null}

          {feedback.knowledge.length > 0 ? (
            <div className="section">
              <div className="section-title">相关知识点</div>
              <div className="row">
                {feedback.knowledge.map((item) => (
                  <span className="chip" key={item}>
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {feedback.doc ? (
            <div className="section">
              <div className="section-title">对应文档</div>
              <Link to={`/docs/${feedback.doc}`}>📖 {docTitle(feedback.doc)}</Link>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="tiny muted" style={{ marginTop: 14, marginBottom: 0 }}>
          选择答案后会立刻显示对错、原因和相关知识点。（桌面端可用键盘 {OPTION_KEYS.slice(0, keys.length).join(" / ")}{" "}
          选择）
        </p>
      )}
    </div>
  );
}

function optionState(
  key: string,
  selected: string | null,
  feedback: FeedbackLike | null,
): "" | "selected" | "correct" | "wrong" {
  if (!feedback) {
    return selected === key ? "selected" : "";
  }
  if (key === feedback.correct_answer) return "correct";
  if (key === feedback.selected) return "wrong";
  return "";
}

function difficultyLabel(difficulty: string): string {
  switch (difficulty) {
    case "easy":
      return "基础";
    case "medium":
      return "进阶";
    case "hard":
      return "较难";
    default:
      return difficulty;
  }
}
