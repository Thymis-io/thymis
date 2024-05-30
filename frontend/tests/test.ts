import { expect, test } from '@playwright/test';

test('index page throws without backend', async ({ page }) => {
	const resp = await page.goto('/');

	expect(resp).not.toBeNull();

	expect(resp.status()).toBe(500); // The backend is not running, so we get a 500 error
});
