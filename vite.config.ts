import path from "path"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

export default defineConfig(({ command }) => ({
  plugins: [tailwindcss()],
  root: ".",
  // Keep /static/ for production build output, but use / in dev.
  base: command === "build" ? "/static/" : "/",
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
    port: 5175,
    strictPort: true,
    origin: "http://localhost:5175",
    cors: true,
  },
}))
