import { defineConfig } from "vite";

export default defineConfig({
  server: {
    host: true,
    port: 5174,
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          phaser: ["phaser"],
        },
      },
    },
  },
});
