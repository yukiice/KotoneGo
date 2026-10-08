import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 开发时把 /api 代理到本地 FastAPI（默认 8000 端口），
// 这样前端代码里统一写相对路径即可，部署时也可以用同样的相对路径。
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // 想换后端地址就改这里（或在前端用 VITE_API_BASE 指定完整地址）
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
