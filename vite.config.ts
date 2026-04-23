import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  root: ".",
  base: "/static/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./frontend"),
    },
  },
  build: {
    manifest: "manifest.json",
    outDir: "frontend/dist",
    rollupOptions: {
      input: "frontend/src/main.tsx",
    },
  },
  server: {
    host: "localhost",
    port: 5173,
    strictPort: true,
    origin: "http://localhost:5173",
    cors: true,
  },
})
