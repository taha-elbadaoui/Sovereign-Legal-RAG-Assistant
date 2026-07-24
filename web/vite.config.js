import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server proxies /api to the Python backend (python serve.py) so
// `npm run dev` works standalone. In production, serve.py itself serves
// the built dist/ folder and handles /api directly on the same port.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
  },
});
