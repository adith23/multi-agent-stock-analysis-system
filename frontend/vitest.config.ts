import path from "node:path";

import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  test: {
    exclude: [...configDefaults.exclude, "tests/e2e/**"],
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    restoreMocks: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: [
        "src/shared/**/*.{ts,tsx}",
        "src/stores/**/*.ts",
        "src/features/**/*.{ts,tsx}",
        "src/widgets/**/*.{ts,tsx}",
      ],
      exclude: [
        "**/index.ts",
        "**/*.types.ts",
        "**/__tests__/**",
        "src/shared/ui/shadcn/**",
        "src/widgets/providers/**",
      ],
      thresholds: {
        "src/shared/**": { branches: 80, functions: 80, lines: 80, statements: 80 },
        "src/stores/**": { branches: 80, functions: 80, lines: 80, statements: 80 },
      },
    },
  },
});
