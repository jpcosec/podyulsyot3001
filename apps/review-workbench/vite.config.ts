/// <reference types="vitest" />
import path from "path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  loadEnv(mode, process.cwd(), "");
  const useMock = process.env.VITE_MOCK === "true";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: useMock
        ? { [path.resolve(__dirname, "src/api/client")]: path.resolve(__dirname, "src/mock/client.ts") }
        : {},
    },
    server: {
      host: "127.0.0.1",
      port: 5173,
    },
    test: {
      environment: 'node',
      include: ['src/**/*.test.ts'],
    },
  };
});
