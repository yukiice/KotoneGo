import type { ReactNode } from "react";

export function ScoreRing({ score, size = 132 }: { score: number; size?: number }) {
  const pct = Math.max(0, Math.min(100, score));
  return (
    <div className="score-ring" style={{ ["--pct" as string]: pct, width: size, height: size }}>
      <div className="inner">
        <strong>{score}</strong>
        <span className="tiny muted">/ 100</span>
      </div>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="feedback section">
      <div className="section-title">{label}</div>
      <div>{children}</div>
    </div>
  );
}

export function Loading({ text = "加载中…" }: { text?: string }) {
  return (
    <div className="empty">
      <span className="spinner" /> <span style={{ marginLeft: 8 }}>{text}</span>
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="alert bad">
      <strong>出错了：</strong> {message}
      {onRetry ? (
        <div style={{ marginTop: 10 }}>
          <button className="btn sm" onClick={onRetry}>
            重试
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Empty({ text, action }: { text: string; action?: ReactNode }) {
  return (
    <div className="empty">
      <p style={{ margin: "0 0 12px" }}>{text}</p>
      {action}
    </div>
  );
}

export function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("zh-CN", { hour12: false });
}

export function formatDuration(seconds: number): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m} 分 ${s} 秒` : `${s} 秒`;
}
