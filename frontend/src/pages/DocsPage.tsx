import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, useNavigate, useParams } from "react-router-dom";
import { Markdown } from "../components/Markdown";
import { DOC_META, extractHeadings, getDoc } from "../content";

export function DocsPage() {
  const { slug = DOC_META[0]!.slug } = useParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const doc = getDoc(slug);

  useEffect(() => {
    // 切换章节后滚到顶部
    window.scrollTo({ top: 0 });
  }, [slug]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return DOC_META;
    return DOC_META.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.summary.toLowerCase().includes(q) ||
        item.slug.includes(q),
    );
  }, [query]);

  if (!doc) {
    return (
      <div className="empty">
        <p>找不到章节「{slug}」。</p>
        <Link className="btn" to="/docs">
          返回文档首页
        </Link>
      </div>
    );
  }

  const headings = extractHeadings(doc.markdown).filter((h) => h.level === 2);
  const index = DOC_META.findIndex((item) => item.slug === slug);
  const prev = index > 0 ? DOC_META[index - 1] : undefined;
  const next = index < DOC_META.length - 1 ? DOC_META[index + 1] : undefined;

  return (
    <div className="docs-layout">
      <aside className="docs-side">
        <input
          type="search"
          placeholder="搜索章节…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ marginBottom: 8 }}
        />
        {filtered.map((item) => (
          <NavLink
            key={item.slug}
            to={`/docs/${item.slug}`}
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            {item.title}
          </NavLink>
        ))}
        {filtered.length === 0 ? <p className="small muted">没有匹配的章节</p> : null}
      </aside>

      <div>
        <div className="docs-mobile-nav">
          <select value={slug} onChange={(event) => navigate(`/docs/${event.target.value}`)}>
            {DOC_META.map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.title}
              </option>
            ))}
          </select>
        </div>

        <article className="docs-body">
          <Markdown>{doc.markdown}</Markdown>

          <div className="row between" style={{ marginTop: 28, gap: 10 }}>
            {prev ? (
              <Link className="btn sm" to={`/docs/${prev.slug}`}>
                ← {prev.title.slice(0, 12)}…
              </Link>
            ) : (
              <span />
            )}
            {next ? (
              <Link className="btn sm" to={`/docs/${next.slug}`}>
                {next.title.slice(0, 12)}… →
              </Link>
            ) : null}
          </div>

          <div className="alert" style={{ marginTop: 18 }}>
            想检验这一章？<Link to={`/exam?topic=${doc.meta.topic}`}>开始本章主题考试</Link>
            <span className="muted small">
              （题目从「{doc.meta.summary}」相关主题随机抽取，答错自动进错题本）
            </span>
          </div>

          {headings.length > 1 ? (
            <div className="toc">
              <div className="section-title tiny muted">本页目录</div>
              {headings.map((heading) => (
                <a key={heading.id} href={`#${heading.id}`}>
                  {heading.text}
                </a>
              ))}
            </div>
          ) : null}
        </article>
      </div>
    </div>
  );
}
