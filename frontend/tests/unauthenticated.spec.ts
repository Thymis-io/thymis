import { test, expect } from '../playwright/fixtures';

// Reset storage state for this file to avoid being authenticated
test.use({ storageState: { cookies: [], origins: [] } });

const colorSchemes = ['light', 'dark'] as const;

colorSchemes.forEach((colorScheme) => {
	test.describe(`Color scheme: ${colorScheme}`, () => {
		test.use({ colorScheme: colorScheme });
		test('index page redirects to login', async ({ page }) => {
			const resp = await page.goto('/');
			expect(resp?.status()).toBe(200);
			expect(resp?.url()).toBe('http://localhost:8000/login');
		});

		test('login page shows login form', async ({ page }) => {
			const resp = await page.goto('/login');
			expect(resp?.status()).toBe(200);

			await expect(page.locator('input[name="username"]')).toBeVisible();
			await expect(page.locator('input[name="password"]')).toBeVisible();
			await expect(page.locator('button[type="submit"]')).toBeVisible();

			await expect(page).toHaveScreenshot();
		});

		test('can login with testadminpassword', async ({ page }) => {
			await page.goto('/login');

			await page.fill('input[name="username"]', 'admin');
			await page.fill('input[name="password"]', 'testadminpassword');
			await page.click('button[type="submit"]');

			await page.waitForURL('http://localhost:8000/overview');

			expect(page.url()).toBe('http://localhost:8000/overview');
		});

		test('visiting overview page without login redirects to login', async ({ page }) => {
			const resp = await page.goto('/overview');

			expect(resp?.status()).toBe(200);
			expect(resp?.url()).toBe('http://localhost:8000/login?redirect=%2Foverview');
		});
	});
});
