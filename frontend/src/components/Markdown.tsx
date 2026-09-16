import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { slugify } from "../content";

/**
 * Markdown 渲染器。
 * - GFM（表格、任务清单、删除线）
 * - 代码高亮（highlight.js）
 * - 标题自动加 id，供 TOC 锚点跳转
 */
const components: Components = {
  h2: ({ children }) => <h2 id={slugify(String(children))}>{children}</h2>,
  h3: ({ children }) => <h3 id={slugify(String(children))}>{children}</h3>,
  a: ({ href, children }) => {
    const external = href?.startsWith("http");
    return (
      <a href={href} target={external ? "_blank" : undefined} rel={external ? "noreferrer" : undefined}>
        {children}
      </a>
    );
  },
  table: ({ children }) => (
    <div className="table-wrap">
      <table>{children}</table>
    </div>
  ),
};

export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { ignoreMissing: true }]]}
        components={components}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
