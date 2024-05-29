import { expect, test } from '@playwright/test';

test('index page redirects to overview', async ({ page }) => {
	await page.goto('/');

	expect(page.url()).toContain('/overview');
});
