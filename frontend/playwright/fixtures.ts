import { test as baseTest, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export * from '@playwright/test';
// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export const test = baseTest.extend<{}, { workerStorageState: string }>({
	// Use the same storage state for all tests in this worker.
	storageState: ({ workerStorageState }, use) => use(workerStorageState),

	// Authenticate once per worker with a worker-scoped fixture.
	workerStorageState: [
		async ({ browser }, use) => {
			// Use parallelIndex as a unique identifier for each worker.
			const id = test.info().parallelIndex;
			const fileName = path.resolve(test.info().project.outputDir, `.auth/${id}.json`);

			if (fs.existsSync(fileName)) {
				// Reuse existing authentication state if any.
				await use(fileName);
				return;
			}

			// Important: make sure we authenticate in a clean environment by unsetting storage state.
			// const page = await browser.newPage({ storageState: undefined });

			// // Acquire a unique account, for example create a new one.
			// // Alternatively, you can have a list of precreated accounts for testing.
			// // Make sure that accounts are unique, so that multiple team members
			// // can run tests at the same time without interference.
			// // const account = await acquireAccount(id);

			// // Perform authentication steps. Replace these actions with your own.

			// await page.goto('http://localhost:8000/auth/logout', { waitUntil: 'domcontentloaded' });
			// await page.goto('http://localhost:8000/login', { waitUntil: 'domcontentloaded' });

			// await page.waitForSelector('input[name="username"]');

			// await page.fill('input[name="username"]', 'admin');
			// await page.fill('input[name="password"]', 'testadminpassword');
			// await page.click('button[type="submit"]');

			await login(page);

			// End of authentication steps.

			await page.context().storageState({ path: fileName });
			await page.close();
			await use(fileName);
		},
		{ scope: 'worker' }
	]
});

export const login = async (page: Page) => {
	await page.goto('http://localhost:8000/auth/logout', { waitUntil: 'domcontentloaded' });
	await page.goto('http://localhost:8000/login', { waitUntil: 'domcontentloaded' });

	await page.waitForSelector('input[name="username"]');

	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');
	await page.waitForURL('http://localhost:8000/overview');
	expect(page.url()).toBe('http://localhost:8000/overview');
};
