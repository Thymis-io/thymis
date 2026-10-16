import { test as baseTest, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export * from '@playwright/test';
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export const test = baseTest.extend<{}, { workerStorageState: string }>({
	// In CI, record a Chrome NetLog per worker (a retry runs in a fresh worker, so it
	// gets its own file). Open with https://netlog-viewer.appspot.com.
	launchOptions: [
		async ({ launchOptions }, use, workerInfo) => {
			if (!process.env.CI) {
				await use(launchOptions);
				return;
			}
			const netlogDir = path.join(path.dirname(workerInfo.config.configFile!), 'playwright-netlog');
			fs.mkdirSync(netlogDir, { recursive: true });
			await use({
				...launchOptions,
				args: [
					...(launchOptions.args ?? []),
					`--log-net-log=${path.join(netlogDir, `worker-${workerInfo.workerIndex}.json`)}`
				]
			});
		},
		{ scope: 'worker' }
	],

	// Use the same storage state for all tests in this worker.
	storageState: ({ workerStorageState }, use) => use(workerStorageState),

	// Authenticate once per worker with a worker-scoped fixture.
	workerStorageState: [
		async ({ browser }, use) => {
			// Use parallelIndex as a unique identifier for each worker.
			const id = test.info().parallelIndex;
			const fileName = path.resolve(test.info().project.outputDir, `.auth/${id}.json`);
			const baseURL = test.info().project.use.baseURL;

			if (fs.existsSync(fileName)) {
				// Reuse existing authentication state if any.
				await use(fileName);
				return;
			}

			// Important: make sure we authenticate in a clean environment by unsetting storage state.
			const page = await browser.newPage({ storageState: undefined, baseURL: baseURL });

			await login(page, baseURL);

			// End of authentication steps.

			await page.context().storageState({ path: fileName });
			await page.close();
			await use(fileName);
		},
		{ scope: 'worker' }
	]
});

export const login = async (page: Page, baseURL?: string) => {
	await page.goto('/auth/logout', { waitUntil: 'domcontentloaded' });
	await page.goto('/login', { waitUntil: 'domcontentloaded' });
	await page.waitForSelector('input[name="username"]');
	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');
	await page.waitForURL('/overview');
	expect(page.url()).toBe(`${baseURL}/overview`);
};
