import { devices, type PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
	webServer: {
		command: 'npm run build && npm run preview',
		port: 4173
	},
	testDir: 'tests',
	testMatch: /(.+\.)?(test|spec)\.[jt]s/,
	...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
		? {
				use: {
					launchOptions: {
						executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH as string
					},
					...devices['Desktop Chrome']
				}
			}
		: {})
};

export default config;
