import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ReportCategory } from "../api/types";

export const REPORT_CATEGORY_OPTIONS: { value: ReportCategory; label: string }[] = [
  { value: "answer_wrong", label: "答案有误" },
  { value: "explanation_wrong", label: "解析不准确" },
  { value: "unclear", label: "题干或选项表述不清" },
  { value: "other", label: "其他" },
];

/**
 * 「这题有问题」纠错入口。切换题目时自动收起并清空状态。
 * 提交后只显示感谢，不展示上报内容，避免误以为已经改了题库。
 */
export function ReportQuestion({ questionId }: { questionId: string }) {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<ReportCategory>("answer_wrong");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setOpen(false);
    setDone(false);
    setError(null);
    setMessage("");
    setCategory("answer_wrong");
  }, [questionId]);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await api.reportQuestion(questionId, { category, message: message.trim() });
      setDone(true);
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败，请稍后再试");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return <div className="tiny muted">已记录，感谢你的反馈。</div>;
  }

  if (!open) {
    return (
      <button className="btn sm ghost" onClick={() => setOpen(true)}>
        这题有问题？
      </button>
    );
  }

  return (
    <div className="report-box">
      <div className="tiny muted" style={{ marginBottom: 6 }}>
        反馈类型
      </div>
      <div className="row" style={{ marginBottom: 8 }}>
        {REPORT_CATEGORY_OPTIONS.map((item) => (
          <button
            key={item.value}
            className={`topic-pill ${category === item.value ? "active" : ""}`}
            onClick={() => setCategory(item.value)}
            disabled={busy}
          >
            {item.label}
          </button>
        ))}
      </div>
      <textarea
        className="note-input"
        rows={2}
        maxLength={500}
        placeholder="补充说明（可不填），例如：正确答案应该是 C，因为……"
        value={message}
        disabled={busy}
        onChange={(event) => setMessage(event.target.value)}
      />
      {error ? (
        <div className="alert bad" style={{ marginTop: 8 }}>
          {error}
        </div>
      ) : null}
      <div className="row" style={{ marginTop: 8 }}>
        <button className="btn sm primary" disabled={busy} onClick={() => void submit()}>
          {busy ? "提交中…" : "提交反馈"}
        </button>
        <button className="btn sm ghost" disabled={busy} onClick={() => setOpen(false)}>
          取消
        </button>
      </div>
    </div>
  );
}
