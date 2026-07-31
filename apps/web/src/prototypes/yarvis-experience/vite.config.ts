import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const previewRoot = fileURLToPath(new URL('./preview', import.meta.url));
const previewOutput = fileURLToPath(new URL('./preview-dist', import.meta.url));

export default defineConfig({
  root: previewRoot,
  plugins: [react()],
  server: { host: '127.0.0.1', port: 4174, strictPort: true },
  build: { outDir: previewOutput, emptyOutDir: true },
});
