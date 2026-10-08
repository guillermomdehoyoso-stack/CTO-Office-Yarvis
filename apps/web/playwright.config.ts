import { defineConfig, devices } from '@playwright/test';

const channel = process.env.D1_BROWSER_CHANNEL;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  outputDir: process.env.PLAYWRIGHT_OUTPUT_DIR || 'test-results',
  reporter: [['list'], ['html', { outputFolder: process.env.PLAYWRIGHT_HTML_REPORT || 'e2e/report', open: 'never' }]],
  use: {
    baseURL: process.env.D1_BROWSER_BASE_URL || 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    ...(channel
      ? {
          channel,
          launchOptions: { args: ['--host-rules=MAP web 127.0.0.1,MAP api 127.0.0.1'] },
        }
      : {}),
    ...devices['Desktop Chrome'],
  },
});
