import { test, expect, type Page } from '../playwright/fixtures';
import { clearState, createConfiguration, deleteAllTasks, expectScreenshot } from './utils';
import * as os from 'os';

test.skip(os.arch() !== 'x64', 'You can only run this suite in an x86 VM');

const waitForTerminalText = async (page: Page, text: string) => {
	return await page.waitForFunction((text: string) => {
		// window.terminals[].buffer.active.getLine(0 up to .length-1).translateToString()
		window.terminals = window.terminals || [];
		let all_buffers = '';
		for (const terminal of window.terminals) {
			for (let i = 0; i < terminal.buffer.active.length; i++) {
				all_buffers += terminal.buffer.active.getLine(i).translateToString();
			}
		}
		return all_buffers.includes(text);
	}, text);
};

const goToDevicesPage = async (page: Page, baseURL?: string) => {
	await page.reload();
	for (let i = 0; i < 5; i++) {
		await page.locator('nav:visible').locator('a', { hasText: 'Devices' }).click();
		await page.waitForURL(new RegExp(baseURL + '/devices'), { timeout: 3000 }).catch(() => {});

		if (page.url() === `${baseURL}/devices`) {
			return;
		}
	}
};

test('Create a x64 vm and run it', async ({ page, request, baseURL }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await createConfiguration(page, 'VM Test x64 1', 'Generic x86-64', []);
	await createConfiguration(page, 'VM Test x64 2', 'Generic x86-64', []);

	// VM tasks can flip order, so we need to allow for some pixel differences
	const updateSnapshots = testInfo.config.updateSnapshots;

	let maxDiffPixels = 256;

	if (updateSnapshots === 'all' || updateSnapshots === 'changed') {
		maxDiffPixels = 32;
	}

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page.locator('h1', { hasText: 'Device Configurations' }).waitFor();

	// find row with 'VM Test x64 1' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'VM Test x64 1' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	// select button "Build and start VM"
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();
	await page.locator('div').filter({ hasText: '4 internal file changes' }).first().waitFor();
	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels
	});
	await page.locator('button').filter({ hasText: 'Commit & Build and start VM' }).first().click();

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page.locator('h1', { hasText: 'Device Configurations' }).waitFor();

	// find row with 'VM Test x64 2' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'VM Test x64 2' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	// wait a few seconds, so the first VM is more likely to finish first
	await page.waitForTimeout(20000);

	// select button "Build and start VM"
	await page.locator('div').filter({ hasText: '0 commit' }).first().waitFor();
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();

	// wait until: 1x on screen "completed", 1x on screen "running"
	test.setTimeout(240000);
	await page
		.locator('td', { hasText: 'completed' })
		.nth(1)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 180000 });
	await expect(page.locator('td', { hasText: 'completed' }).nth(1)).toBeVisible();

	await page
		.locator('td', { hasText: 'running' })
		.nth(1)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 120000 });
	await expect(page.locator('td', { hasText: 'running' }).nth(1)).toBeVisible();

	// go to "Devices" page and wait until "Connected" is shown twice
	await goToDevicesPage(page, baseURL);
	await page.locator('td', { hasText: 'Connected' }).nth(1).waitFor({ timeout: 90000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels
	});

	await page.getByPlaceholder('Search...').click();
	await page.locator('#global-search-dropdown').locator('a', { hasText: 'VM Test x64 1' }).click();

	await waitForTerminalText(page, '[root@vm-test-x64-1:~]#');

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels
	});

	// add a CustomModule and configure services.openssh.banner to "Hello World", then deploy and then take another screenshot

	// go to "Configure" tab
	await page.locator('a', { hasText: 'Configure' }).first().click();

	// click on "Add Module" button
	const addModuleButton = page.locator('#add-module').first();
	await addModuleButton.click();

	// select "CustomModule" from dropdown
	const addCustomModuleButton = page.locator('button').filter({ hasText: 'Custom Module' });
	await addCustomModuleButton.click();

	// fill in the form input "Freeform Settings"
	await page.locator('p', { hasText: 'Freeform Settings' }).waitFor();
	const freeformSettingsInput = page.locator('textarea').first();
	await freeformSettingsInput.fill(
		'programs.bash.promptInit = "PS1=\\"\\[`cat /run/thymis/secret.txt`Hello World Custom Prompt\\] \\"";services.openssh.settings.PrintLastLog = "no";'
	);

	// Edit core device module too
	await page.locator('p', { hasText: 'Core Device Configuration' }).click();
	await page.getByRole('button', { name: 'Add Secret' }).click();
	await page.getByRole('button', { name: 'Create Secret' }).nth(1).click();
	await page.getByPlaceholder('No name').fill('secret.txt');
	await page.getByLabel('Value').fill('THIS IS A SECRET');
	await page.getByRole('button', { name: 'Save' }).click();

	// path
	await page.getByPlaceholder('Secret Path').fill('/run/thymis/secret.txt');

	// expect(false).toBe(true, 'This test is not finished yet');

	// click on "Deploy" button
	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await deployButton.click();

	// add the second VM to the deployment
	await page.locator('input').nth(2).locator('..').click();
	await page.locator('li').filter({ hasText: 'VM Test x64 2' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 1500
	});

	// Click on new "Deploy" button in modal to confirm
	const deployButtonModal = page.getByRole('dialog').locator('button', { hasText: 'Deploy' });
	await deployButtonModal.click();

	// Wait for a fifth "completed" status
	await page.locator('td', { hasText: 'completed' }).nth(4).waitFor({ timeout: 60000 });

	// Navigate back to "Details" tab
	await page.locator('a', { hasText: 'Details' }).first().click();
	await page.locator('p', { hasText: 'Deployed:' }).first().waitFor();

	await waitForTerminalText(page, '[THIS IS A SECRETHello World Custom Prompt]');

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels
	});

	// Now, navigate to "Devices" page using sidebar and take a screenshot
	await goToDevicesPage(page, baseURL);

	// Wait for 2 "Connected" statuses
	await page.locator('td', { hasText: 'Connected' }).nth(1).waitFor({ timeout: 90000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels
	});

	// now, switch the first device to usb installer, download the image and check for download
	await page.getByPlaceholder('Search...').click();
	await page.locator('#global-search-dropdown').locator('a', { hasText: 'VM Test x64 1' }).click();

	// configure the device to usb installer
	await page.locator('a', { hasText: 'Configure' }).first().click();
	// select "Core Device Configuration"
	await page.locator('a', { hasText: 'Core Device Configuration' }).first().click();
	// select div with text "Image Format", find the select element and select "usb-installer"
	await page.getByRole('combobox').nth(1).selectOption({ value: 'usb-stick-installer' });
	// find download button and click on it
	await page.locator('button').filter({ hasText: 'Download Device Image' }).first().click();
	await page.locator('div').filter({ hasText: '1 internal file changes' }).first().waitFor();
	await page
		.locator('button')
		.filter({ hasText: 'Commit & Download Device Image' })
		.first()
		.click();
	await page.waitForEvent('download');
});
