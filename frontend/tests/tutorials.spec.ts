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
});
