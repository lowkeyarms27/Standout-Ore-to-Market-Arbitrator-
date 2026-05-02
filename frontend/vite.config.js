import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5177,
    proxy: {
      '/api/ws': { target: 'ws://127.0.0.1:8003', ws: true },
      '/api': { target: 'http://127.0.0.1:8003', changeOrigin: true },
    },
  },
  build: { outDir: 'dist' },
})
