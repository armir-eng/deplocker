import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import path from "path";
import react from "@vitejs/plugin-react";

export default ({ mode }: { mode: string }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return defineConfig({
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    define: {
      API_URL: JSON.stringify(env.API_URL ?? "http://localhost:8000"),
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.ts"],
      include: [
        "src/test/unit/**/*.test.{ts,tsx}",
        "src/test/integration/**/*.test.{ts,tsx}",
        "src/test/e2e/**/*.test.{ts,tsx}",
      ],
    },
  });
};
