import { expect, test, type PageAssertionsToHaveScreenshotOptions } from '../playwright/fixtures';
import {
	clearState,
	deleteAllTasks,
	expectScreenshot,
	expectScreenshotWithHighlight
} from './utils';

const screenshotOptions: PageAssertionsToHaveScreenshotOptions = {
	mask: [],
	maxDiffPixels: 200
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

	const downloadImageButton = page.locator('button').filter({ hasText: 'Download Device Image' });
	await page.mouse.wheel(0, -500);
	await expectScreenshotWithHighlight(
		page,
		downloadImageButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);

	await downloadImageButton.click();
	const commitButton = page.locator('button').filter({ hasText: 'Commit & Download Device Image' });

	await expectScreenshotWithHighlight(
		page,
		commitButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);
});

test('deploy update', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	const configName = 'Test Configuration';

	page.setViewportSize({ width: 1600, height: 900 });

	await clearState(page, request);
	await deleteAllTasks(page, request);

	const navConfigLocator = page.locator('nav:visible').locator('a', { hasText: 'Configs' });
	await navConfigLocator.click();

	const createConfigButton = page.locator('button').filter({ hasText: 'Create New Configuration' });
	await createConfigButton.click();

	const displayNameInput = page.locator('#display-name').first();
	await displayNameInput.fill(configName);
	await displayNameInput.blur();

	const deviceTypeSelect = page.locator('#device-type').first();
	await deviceTypeSelect.selectOption({ label: 'Generic x86-64' });

	const saveButton = page.locator('button').filter({ hasText: 'create device configuration' });
	await saveButton.click();

	const configureButton = page.locator('tr').getByRole('button', { name: 'Configure' });
	await configureButton.click();
	await page.waitForURL('/configuration/edit*');

	const imageFormatSelect = page
		.locator('p', { hasText: 'Image Format' })
		.locator('..')
		.locator('select')
		.first();
	await imageFormatSelect.selectOption({ label: 'NixOS VM' });

	const runVMButton = page.locator('button', { hasText: 'Build and start VM' });
	await runVMButton.click();
	const commitButton = page.locator('button').filter({ hasText: 'Commit & Build and start VM' });
	await commitButton.click();

	// wait until: 1x on screen "completed", 1x on screen "running"
	test.setTimeout(360000);
	await page
		.locator('td', { hasText: 'completed' })
		.nth(0)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 360000 });
	await expect(page.locator('td', { hasText: 'completed' }).nth(0)).toBeVisible();

	await page
		.locator('td', { hasText: 'running' })
		.nth(0)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 360000 });
	await expect(page.locator('td', { hasText: 'running' }).nth(0)).toBeVisible();

	await navConfigLocator.click();

	const updateButton = page.locator('button').filter({ hasText: 'Update' });
	await expectScreenshotWithHighlight(
		page,
		updateButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);

	await updateButton.click();
	await page.locator('body').click(); // click to remove focus from the button

	await page
		.locator('td', { hasText: 'completed' })
		.nth(1)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 30000 });

	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await expectScreenshotWithHighlight(
		page,
		deployButton,
		testInfo,
		screenshotCounter,
		screenshotOptions
	);
	await deployButton.click();
	await page.locator('body').click(); // click to remove focus from the button

	const configsToDeploy = page
		.getByText('Tags/configs to deploy')
		.locator('..')
		.locator('input')
		.first();

	await expectScreenshotWithHighlight(
		page,
		configsToDeploy.locator('..'),
		testInfo,
		screenshotCounter,
		screenshotOptions
	);

	await configsToDeploy.fill(configName);
	const deployButton2 = page.locator('button').filter({ hasText: 'Deploy' }).nth(1);
	await deployButton2.click();

	await page
		.locator('td', { hasText: 'completed' })
		.nth(3)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 30000 });

	await expectScreenshot(page, testInfo, screenshotCounter, screenshotOptions);
});
