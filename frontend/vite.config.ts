import { defineConfig } from 'vite'

export default defineConfig({
  base: '/static/',   // <--- ADD THIS LINE
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/upload': 'http://127.0.0.1:8000',
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
