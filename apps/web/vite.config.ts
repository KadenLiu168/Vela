import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  build: {
    manifest: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (/[/\\]node_modules[/\\](react|react-dom|scheduler)[/\\]/.test(id)) {
            return "react-vendor";
          }
        }
      }
    }
  },
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts"
  }
});
