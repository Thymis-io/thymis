import { test, expect } from '../playwright/fixtures';

// Reset storage state for this file to avoid being authenticated
test.use({ storageState: { cookies: [], origins: [] } });

test('index page redirects to login', async ({ page }) => {
	const resp = await page.goto('/');

	expect(resp).not.toBeNull();
	if (resp === null) {
		throw new Error('resp is null');
	}
	expect(resp.status()).toBe(200);
	expect(resp.url()).toBe('http://localhost:8000/login');
});

test('login page shows login form', async ({ page }) => {
	const resp = await page.goto('/login');

	expect(resp).not.toBeNull();
	if (resp === null) {
		throw new Error('resp is null');
	}
	expect(resp.status()).toBe(200);

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

test('overview page shows overview', async ({ page }) => {
	await page.goto('/login');

	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');

	await page.waitForURL('http://localhost:8000/overview');

	// we expect the texts "Devices", "Tags", "Modules" each to be present
	expect(page.getByText('Devices')).not.toBeNull();
	expect(page.getByText('Tags')).not.toBeNull();
	expect(page.getByText('Modules')).not.toBeNull();

	await expect(page).toHaveScreenshot();
});

test('visiting overview page without login redirects to login', async ({ page }) => {
	const resp = await page.goto('/overview');

	expect(resp).not.toBeNull();
	if (resp === null) {
		throw new Error('resp is null');
	}
	expect(resp.status()).toBe(200);
	expect(resp.url()).toBe('http://localhost:8000/login?redirect=%2Foverview');
});
