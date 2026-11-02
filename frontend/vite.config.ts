// frontend/vite.config.ts
import { defineConfig } from 'vite'

export default defineConfig({
  build: {
    outDir: '../static',   // FastAPI will mount this
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/upload': 'http://127.0.0.1:8000',
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
