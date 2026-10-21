import { defineConfig } from 'vite';

export default defineConfig({
  esbuild: { jsx: 'automatic' },
  server: { allowedHosts: ['terminal.local'] },
});
