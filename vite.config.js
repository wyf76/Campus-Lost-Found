import { defineConfig } from 'vite';

// Preserve the browser host so Django's CSRF origin check sees the same origin.
const django = { target: 'http://127.0.0.1:8000', changeOrigin: false };
const proxy = { '/api': django, '/media': django };

export default defineConfig(({ command }) => ({
  // Production assets are served by Django and WhiteNoise under /static/.
  base: command === 'build' ? '/static/' : '/',
  esbuild: { jsx: 'automatic' },
  server: { allowedHosts: ['terminal.local'], proxy },
  preview: { allowedHosts: ['terminal.local'], proxy },
}));
