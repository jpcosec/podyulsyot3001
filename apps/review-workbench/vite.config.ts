import path from "path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const useMock = env.VITE_MOCK === "true";

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: useMock
        ? { "/src/api/client": path.resolve(__dirname, "src/mock/client.ts") }
        : {},
    },
    server: {
      host: "127.0.0.1",
      port: 5173,
    },
  };
});
