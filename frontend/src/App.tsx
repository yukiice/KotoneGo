import { Link, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { DocsPage } from "./pages/DocsPage";
import { ExamResultPage, ExamRunnerPage, ExamSetupPage } from "./pages/ExamPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { StatsPage } from "./pages/StatsPage";
import { WrongBookPage } from "./pages/WrongBookPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/docs" element={<DocsPage />} />
        <Route path="/docs/:slug" element={<DocsPage />} />
        <Route path="/exam" element={<ExamSetupPage />} />
        <Route path="/exam/:examId" element={<ExamRunnerPage />} />
        <Route path="/result/:examId" element={<ExamResultPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/wrong" element={<WrongBookPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route
          path="*"
          element={
            <div className="empty">
              <p>页面不存在。</p>
              <Link className="btn" to="/">
                回到首页
              </Link>
            </div>
          }
        />
      </Route>
    </Routes>
  );
}
