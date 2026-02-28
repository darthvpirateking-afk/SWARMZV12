import { defineConfig } from 'vite';
import preact from '@preact/preset-vite';

export default defineConfig({
  plugins: [preact()],
  server: {
    port: 5173,
    proxy: {
      '/v1/canonical': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
      '/v1': {
        target: 'http://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
