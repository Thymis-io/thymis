import { test, expect } from '../playwright/fixtures';
import { expectScreenshot, expectScreenshotWithHighlight } from './utils';
// Reset storage state for this file to avoid being authenticated
test.use({ storageState: { cookies: [], origins: [] } });

test('index page redirects to login', async ({ page }) => {
	const resp = await page.goto('/');
	expect(resp?.status()).toBe(200);
	expect(resp?.url()).toBe('http://localhost:8000/login');
});

test('toolbar links work', async ({ page }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await page.goto('/');

	await expect(page.url()).toBe('http://localhost:8000/login');

	const rootLink = page.locator('a').filter({ hasText: 'Thymis' });
	await expectScreenshotWithHighlight(page, rootLink, testInfo, screenshotCounter);
	await rootLink.click();

	await expect(page.url()).toBe('http://localhost:8000/login');

	const homepageLink = page.locator('a').filter({ hasText: 'Homepage' });
	await expectScreenshotWithHighlight(page, homepageLink, testInfo, screenshotCounter);
	await homepageLink.click();

	await expect(page.url()).toBe('https://thymis.io/en');

	await page.goBack();
	await page.mouse.click(0, 0);
	await expect(page.url()).toBe('http://localhost:8000/login');

	const docsLink = page.locator('a').filter({ hasText: 'Documentation' });
	await expectScreenshotWithHighlight(page, docsLink, testInfo, screenshotCounter);
	await docsLink.click();

	await expect(page.url()).toBe('https://docs.thymis.io/');

	await page.goBack();
	await expect(page.url()).toBe('http://localhost:8000/login');
});

test('login page shows login form', async ({ page }, testInfo) => {
	const screenshotCounter = { count: 0 };
	const resp = await page.goto('/login');
	expect(resp?.status()).toBe(200);

	await expect(page.locator('input[name="username"]')).toBeVisible();
	await expect(page.locator('input[name="password"]')).toBeVisible();
	await expect(page.locator('button[type="submit"]')).toBeVisible();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('can login with testadminpassword and redirect to login', async ({ page }) => {
	await page.goto('/login');

	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');

	await page.waitForURL('http://localhost:8000/overview');

	expect(page.url()).toBe('http://localhost:8000/overview');
});

test('can redirect to page after login', async ({ page }) => {
	await page.goto('/devices');

	await page.waitForURL(/http:\/\/localhost:8000\/login\?redirect=.+\/devices/);

	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');

	await page.waitForURL('http://localhost:8000/devices');

	expect(page.url()).toBe('http://localhost:8000/devices');
});

test('visiting overview page without login redirects to login', async ({ page }) => {
	const resp = await page.goto('/overview');

	expect(resp?.status()).toBe(200);
	expect(resp?.url()).toMatch(/http:\/\/localhost:8000\/login\?redirect=.+\/overview/);
});

test('highlight login button', async ({ page }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await page.goto('/login');

	const loginButton = page.locator('button[type="submit"]');
	await expect(loginButton).toBeVisible();
	await expectScreenshotWithHighlight(page, loginButton, testInfo, screenshotCounter);
});
