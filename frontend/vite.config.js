import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // target: "http://182.92.78.224:8800",
        target: "http://182.92.78.224:8800",
        changeOrigin: true,
      },
    },
  },
});
