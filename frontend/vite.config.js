import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: true, // 监听所有地址（含 127.0.0.1 IPv4 与 localhost IPv6）
    port: 5173,
    proxy: {
      // 开发环境将 /api 代理到后端 FastAPI
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 头像等静态资源
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
    // 忽略编辑器/工具产生的临时文件与隐藏文件，避免文件锁导致 watcher 崩溃
    watch: {
      ignored: ['**/.??*', '**/*.tmp', '**/*.tmpdir/**', '**/node_modules/**'],
    },
  },
})