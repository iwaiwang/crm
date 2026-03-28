import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

const apiTarget = process.env.CRM_API_TARGET || 'http://127.0.0.1:8002'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        ws: true,
        // 不走系统代理
        agent: false,
      },
      '/uploads': {
        target: apiTarget,
        changeOrigin: true,
        agent: false,
      },
    },
  },
})
