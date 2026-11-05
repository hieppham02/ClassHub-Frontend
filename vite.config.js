import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";
import { readFileSync } from "node:fs";

// https://vitejs.dev/config/
export default defineConfig(({ command, isPreview }) => ({
  plugins: [vue(), tailwindcss()],
  server: command === "serve" && !isPreview ? {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    https: {
      cert: readFileSync(new URL("./.cert/localhost.pem", import.meta.url)),
      key: readFileSync(new URL("./.cert/localhost-key.pem", import.meta.url)),
    },
    proxy: {
      "/api": {
        target: "http://localhost:5146",
        changeOrigin: true,
      },
      "/hub": {
        target: "http://localhost:5146",
        changeOrigin: true,
        ws: true,
      },
    },
  } : undefined,
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
}));
