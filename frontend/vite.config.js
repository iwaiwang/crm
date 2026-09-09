import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { execSync } from 'child_process'

const apiTarget = process.env.CRM_API_TARGET || 'http://127.0.0.1:8002'

function getGitHash() {
  try {
    return execSync('git rev-parse --short HEAD').toString().trim()
  } catch {
    return process.env.VITE_GIT_HASH || 'dev'
  }
}

function getBuildId() {
  const now = new Date()
  return `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}-${String(now.getHours()).padStart(2,'0')}${String(now.getMinutes()).padStart(2,'0')}`
}

const buildTime = new Date().toISOString().slice(0, 19).replace('T', ' ')

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify('1.0.0'),
    __BUILD_TIME__: JSON.stringify(buildTime),
    __GIT_HASH__: JSON.stringify(getGitHash()),
    __BUILD_ID__: JSON.stringify(getBuildId()),
  },
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
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
