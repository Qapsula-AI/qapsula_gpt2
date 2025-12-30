import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../static',  // Вывод в app/static/ для обслуживания FastAPI
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  server: {
    port: 5173,
    host: true,  // Слушать на всех интерфейсах (0.0.0.0)
    strictPort: false,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      'host.docker.internal',  // Разрешить запросы из Docker
    ],
    proxy: {
      // Проксирование API запросов к FastAPI серверу
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})