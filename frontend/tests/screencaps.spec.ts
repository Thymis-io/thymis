import { test, expect } from '../playwright/fixtures';

test('shows devices', async ({ page }) => {
	page.on('console', (msg) => {
		console.log(`Error text: "${msg.text()}"`);
	});
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
