import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build', // Django/Whitenoise expects the build in this folder
  },
  server: {
    port: 3000,
  },
  define: {
    // Polyfill for any library that still references process.env
    'process.env': {},
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
