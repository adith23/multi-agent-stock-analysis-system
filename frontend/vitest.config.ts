import path from "node:path";

import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  test: {
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
    },
  },
});
