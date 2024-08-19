import { expect, test } from '@playwright/test';

test('index page redirects to login', async ({ page }) => {
	const resp = await page.goto('/');

	expect(resp).not.toBeNull();
	if (resp === null) {
		throw new Error('resp is null');
	}
	expect(resp.status()).toBe(200);
	expect(resp.url()).toBe('http://localhost:8000/login');
});
