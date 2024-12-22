import { test, expect } from '../playwright/fixtures';

test('shows devices', async ({ page }) => {
	page.on('console', (msg) => {
		console.log(`Error text: "${msg.text()}"`);
	});
	const resp = await page.goto('/devices');

	// 200 OK is expected
	expect(resp).not.toBeNull();
	if (resp === null) {
		throw new Error('resp is null');
	}
	expect(resp.status()).toBe(200);

	await expect(page).toHaveScreenshot();

	// We can add Devices
	const addDeviceButton = page.locator('button').filter({ hasText: 'Create New Device' });
	expect(addDeviceButton).not.toBeNull();
	await addDeviceButton.click();

	// expect (await page.locator('input').count()).toBe(3);
	// print the input fields
	// await expect(page.locator('input')).toHaveCount(4);

	await expect(page).toHaveScreenshot();
});
