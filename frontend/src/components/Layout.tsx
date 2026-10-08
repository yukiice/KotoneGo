import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";

const NAV = [
  { to: "/", label: "首页" },
  { to: "/docs", label: "语法文档" },
  { to: "/exam", label: "开始考试" },
  { to: "/history", label: "考试记录" },
  { to: "/wrong", label: "错题本" },
  { to: "/stats", label: "统计" },
];

export function Layout() {
  const { pathname } = useLocation();

  // 路由切换时回到顶部（移动端体验）
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);

  return (
    <div className="app">
      <header className="header">
        <div className="container header-inner">
          <Link to="/" className="brand">
            <span className="brand-mark">琴</span>
            <span>
              KotoneGo
              <br />
              <small>Python 学习平台</small>
            </span>
          </Link>
          <nav className="nav">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"}>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="main">
        <Outlet />
      </main>

      <footer className="footer">
        为 React/TS 开发者准备的 Python 教程与考试系统 · 数据保存在本地 SQLite
      </footer>
    </div>
  );
}
