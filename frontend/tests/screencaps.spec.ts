import { test, expect } from '../playwright/fixtures';

test.describe.configure({ mode: 'serial' });

const colorSchemes = ['light', 'dark'] as const;

colorSchemes.forEach((colorScheme) => {
	test.describe(`Color scheme: ${colorScheme}`, () => {
		test.use({ colorScheme: colorScheme });

		test('overview page shows overview', async ({ page }) => {
			await page.goto('/login');

			await page.fill('input[name="username"]', 'admin');
			await page.fill('input[name="password"]', 'testadminpassword');
			await page.click('button[type="submit"]');

			await page.waitForURL('http://localhost:8000/overview');

			await expect(page).toHaveScreenshot();
		});

		test('shows devices', async ({ page }) => {
			const resp = await page.goto('/devices');

			// 200 OK is expected
			expect(resp?.status()).toBe(200);
			await expect(page).toHaveScreenshot();

			// We can add Devices
			const addDeviceButton = page.locator('button').filter({ hasText: 'Create New Device' });
			await addDeviceButton.click();

			await expect(page).toHaveScreenshot();

			// select id display-name input and fill it with 'My Device 1'
			const displayNameInput = page.locator('#display-name').first();
			await displayNameInput.fill('My Device 1');

			const deviceTypeSelect = page.locator('#device-type').first();
			await deviceTypeSelect.selectOption({ label: 'Raspberry Pi 4' });

			const saveButton = page.locator('button').filter({ hasText: 'Create device' });
			await saveButton.click();

			await expect(page).toHaveScreenshot();

			// go to device details page, delete device
			const viewDetailsButton = page.locator('a', { hasText: 'View Details' }).first();
			await viewDetailsButton.click();

			await expect(page).toHaveScreenshot();

			const deleteButton = page.locator('button').filter({ hasText: 'Delete' });
			await deleteButton.click();

			await expect(page).toHaveScreenshot();

			const confirmButton = page.locator('button').filter({ hasText: 'Delete' }).nth(0);
			await confirmButton.click();

			await expect(page).toHaveScreenshot();

			const devicesNav = page.locator('a', { hasText: 'Devices' }).locator('visible=true').first();
			await devicesNav.click();

			await expect(page).toHaveScreenshot();
		});

		test('explores more pages', async ({ page }) => {
			// Navigate to the Devices page
			await page.goto('/devices');
			await expect(page).toHaveScreenshot();

			// Navigate to the Tags page
			const tagsNav = page.locator('a', { hasText: 'Tags' }).locator('visible=true').first();
			await tagsNav.click();
			await expect(page).toHaveScreenshot();

			// Navigate to the History page
			const historyNav = page.locator('a', { hasText: 'History' }).locator('visible=true').first();
			await historyNav.click();
			await expect(page).toHaveScreenshot();

			// Navigate to the External Repositories page
			const externalReposNav = page
				.locator('a', { hasText: 'External Repositories' })
				.locator('visible=true')
				.first();
			await externalReposNav.click();
			await expect(page).toHaveScreenshot();
		});
	});
});
