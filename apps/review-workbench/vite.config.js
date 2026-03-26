import path from "path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(function (_a) {
    var _b;
    var mode = _a.mode;
    loadEnv(mode, process.cwd(), "");
    var useMock = process.env.VITE_MOCK === "true";
    return {
        plugins: [react()],
        resolve: {
            alias: Object.assign({ "@": path.resolve(__dirname, "src") }, (useMock
                ? (_b = {}, _b[path.resolve(__dirname, "src/api/client")] = path.resolve(__dirname, "src/mock/client.ts"), _b)
                : {})),
        },
        server: {
            host: "127.0.0.1",
            port: 5173,
        },
    };
});
