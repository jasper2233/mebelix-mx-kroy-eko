import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: backend http://localhost:8000 (uvicorn), frontend http://localhost:5173
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": { target: process.env.MEBELIX_API ?? "http://localhost:8000", changeOrigin: true } },
  },
  build: { outDir: "dist", sourcemap: false, chunkSizeWarningLimit: 2500 },
});
