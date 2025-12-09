import { defineConfig } from 'vite';

export default defineConfig({
  root: 'frontend',
  publicDir: '../public',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: './frontend/index.html',
        builder: './frontend/builder.html'
      }
    }
  },
  server: {
    port: 3000,
    open: true
  }
});
