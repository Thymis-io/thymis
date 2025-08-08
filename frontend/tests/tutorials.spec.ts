import {
	test,
	expect,
	type Page,
	type PageAssertionsToHaveScreenshotOptions
} from '../playwright/fixtures';
import {
	clearState,
	deleteAllTasks,
	expectScreenshot,
	expectScreenshotWithHighlight
} from './utils';

const screenshotOptions: PageAssertionsToHaveScreenshotOptions = {
	mask: []
};

test('initial device provisioning', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	const configName = 'Test Configuration';

	page.setViewportSize({ width: 1600, height: 900 });

	await clearState(page, request);
	await deleteAllTasks(page, request);

	const navConfigLocator = page.locator('nav:visible').locator('a', { hasText: 'Configs' });
	await navConfigLocator.click();

	const createConfigButton = page.locator('button').filter({ hasText: 'Create New Configuration' });
	await expectScreenshotWithHighlight(
		page,
		createConfigButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);
	await createConfigButton.click();

	const displayNameInput = page.locator('#display-name').first();
	await displayNameInput.fill(configName);
	await displayNameInput.blur();

	const deviceTypeSelect = page.locator('#device-type').first();
	await deviceTypeSelect.selectOption({ label: 'Raspberry Pi 4' });

	await expectScreenshot(page, testInfo, screenshotCounter, screenshotOptions);

	const saveButton = page.locator('button').filter({ hasText: 'create device configuration' });
	await saveButton.click();

	const configureButton = page.locator('tr').getByRole('button', { name: 'Configure' });
	await expectScreenshotWithHighlight(
		page,
		configureButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);

	await configureButton.click();
	await page.waitForURL('/configuration/edit*');

	const wifiSSID = page.locator('p', { hasText: 'WiFi SSID' }).first();
	await wifiSSID.hover();
	await page.mouse.wheel(0, 50);

	const wifiSSIDInput = wifiSSID.locator('..').locator('input').first();
	const wifiPassword = page
		.locator('p', { hasText: 'WiFi Password' })
		.locator('..')
		.locator('input')
		.first();

	await expectScreenshotWithHighlight(
		page,
		[wifiSSIDInput, wifiPassword],
		testInfo,
		screenshotCounter,
		screenshotOptions
	);

	await wifiSSIDInput.fill('MyWifi');
	await wifiPassword.fill('MyPassword');
	await wifiPassword.blur();

	await expectScreenshot(page, testInfo, screenshotCounter, screenshotOptions);

	const saveConfigButton = page.locator('button').filter({ hasText: 'Download Device Image' });
	await page.mouse.wheel(0, -500);
	await expectScreenshotWithHighlight(
		page,
		saveConfigButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);
});
