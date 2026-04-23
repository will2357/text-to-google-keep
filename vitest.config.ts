import path from "path"
import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["frontend/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["frontend/components/**/*.tsx", "frontend/pages/**/*.tsx", "frontend/lib/**/*.ts"],
      thresholds: {
        lines: 90,
        statements: 90,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./frontend"),
    },
  },
})
