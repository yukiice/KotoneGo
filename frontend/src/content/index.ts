/**
 * 文档清单。
 * 新增章节：把 .md 放到 content/docs/ 下，然后在这里加一条即可。
 * slug 要和题库 JSON 里的 doc 字段一致（用于“去练习本章”和错题跳转）。
 */

import type { ComponentType } from "react";

export interface DocMeta {
  slug: string;
  title: string;
  summary: string;
  /** 对应的考试主题（用于“练这一章”） */
  topic: string;
}

export const DOC_META: DocMeta[] = [
  { slug: "01-hello-python", title: "01 起点：Python 与前端世界的差异", summary: "运行方式、虚拟环境、工具链对照", topic: "basics" },
  { slug: "02-syntax-basics", title: "02 基础语法：缩进、变量、输入输出", summary: "缩进即语法、命名、print/input", topic: "basics" },
  { slug: "03-data-types", title: "03 数据类型与类型转换", summary: "int/float/bool/None/str、可变性", topic: "types" },
  { slug: "04-operators", title: "04 运算符与表达式", summary: "算术、比较、逻辑、位运算、优先级", topic: "operators" },
  { slug: "05-strings", title: "05 字符串处理", summary: "切片、方法、f-string、性能", topic: "strings" },
  { slug: "06-collections", title: "06 列表、元组、字典、集合", summary: "四种容器与复制语义", topic: "collections" },
  { slug: "07-control-flow", title: "07 条件与循环", summary: "if/for/while、enumerate、match", topic: "control" },
  { slug: "08-functions", title: "08 函数与作用域", summary: "参数、默认值陷阱、LEGB、闭包", topic: "functions" },
  { slug: "09-comprehensions", title: "09 推导式", summary: "list/set/dict 推导式与生成器表达式", topic: "comprehensions" },
  { slug: "10-iterators-generators", title: "10 迭代器与生成器", summary: "迭代协议、yield、itertools", topic: "iterators" },
  { slug: "11-oop", title: "11 面向对象", summary: "类、继承、魔术方法、dataclass", topic: "oop" },
  { slug: "12-exceptions", title: "12 异常处理", summary: "try/except、异常链、with", topic: "exceptions" },
  { slug: "13-modules-stdlib", title: "13 模块、包与标准库", summary: "import 机制、标准库、pip", topic: "modules" },
  { slug: "14-files-json", title: "14 文件与数据格式", summary: "文件读写、pathlib、JSON/CSV", topic: "files" },
  { slug: "15-typing", title: "15 类型注解与 mypy", summary: "注解、泛型、Pydantic、严格模式", topic: "typing" },
  { slug: "16-decorators-closures", title: "16 闭包与装饰器", summary: "高阶函数、wraps、functools", topic: "decorators" },
  { slug: "17-async", title: "17 异步编程（asyncio）", summary: "协程、gather、阻塞陷阱", topic: "async" },
  { slug: "18-pitfalls-vs-js", title: "18 易错点与 JS/TS 迁移指南", summary: "十大坑、空值模型、速查替换表", topic: "pitfalls" },
];

const modules = import.meta.glob("./docs/*.md", { query: "?raw", import: "default", eager: true }) as Record<
  string,
  string
>;

const CONTENT: Record<string, string> = Object.fromEntries(
  Object.entries(modules).map(([path, text]) => [path.replace("./docs/", "").replace(/\.md$/, ""), text]),
);

export function getDoc(slug: string): { meta: DocMeta; markdown: string } | undefined {
  const meta = DOC_META.find((item) => item.slug === slug);
  const markdown = CONTENT[slug];
  if (!meta || !markdown) return undefined;
  return { meta, markdown };
}

export function docTitle(slug: string): string {
  return DOC_META.find((item) => item.slug === slug)?.title ?? slug;
}

export function docTopic(slug: string): string | undefined {
  return DOC_META.find((item) => item.slug === slug)?.topic;
}

/** 文档里的标题抽成目录（用于右侧 TOC） */
export function extractHeadings(markdown: string): { level: number; text: string; id: string }[] {
  return markdown
    .split("\n")
    .filter((line) => /^#{2,3}\s/.test(line))
    .map((line) => {
      const level = (line.match(/^#+/) ?? ["##"])[0].length;
      const text = line.replace(/^#+\s*/, "").trim();
      return { level, text, id: slugify(text) };
    });
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .trim()
    .replace(/\s+/g, "-");
}

export type { ComponentType };
