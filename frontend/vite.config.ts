import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,  // 使用 Vite 默认端口
    proxy: {
      '/api': {
        target: 'http://localhost:8004',  // 更新为正确的后端端口
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Vercel部署时关闭sourcemap以减少构建时间
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd']
        }
      }
    }
  },
  base: '/' // 确保正确的基础路径
})