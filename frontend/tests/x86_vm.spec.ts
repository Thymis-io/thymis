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

test('Create a x64 vm and run it', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await createConfiguration(page, 'VM Test x64 1', 'Generic x86-64', []);
	await createConfiguration(page, 'VM Test x64 2', 'Generic x86-64', []);

	await page.goto('/configuration/list');

	// find row with 'VM Test x64 1' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'VM Test x64 1' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	// select button "Build and start VM"
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	// find row with 'VM Test x64 2' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'VM Test x64 2' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	// select button "Build and start VM"
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();

	// wait until: 1x on screen "completed", 1x on screen "running"
	test.setTimeout(360000);
	await page
		.locator('td', { hasText: 'completed' })
		.nth(1)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 360000 });
	await expect(page.locator('td', { hasText: 'completed' }).nth(1)).toBeVisible();

	await page
		.locator('td', { hasText: 'running' })
		.nth(1)
		.or(page.locator('td', { hasText: 'failed' }).first())
		.waitFor({ timeout: 360000 });
	await expect(page.locator('td', { hasText: 'running' }).nth(1)).toBeVisible();

	// go to "Devices" page and wait until "Connected" is shown twice
	// await page.goto('/devices');
	await page.locator('a', { hasText: 'Devices' }).locator('visible=true').first().click();
	await page.locator('td', { hasText: 'Connected' }).nth(1).waitFor({ timeout: 60000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 128
	});

	await page.getByPlaceholder('Search...').click();
	await page.locator('#global-search-dropdown').locator('a', { hasText: 'VM Test x64 1' }).click();

	await waitForTerminalText(page, '[root@vm-test-x64-1:~]#');

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 128
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
	const freeformSettingsInput = page.locator('textarea').first();
	await freeformSettingsInput.fill(
		'programs.bash.promptInit = "PS1=\\"\\[Hello World Custom Prompt\\] \\"";services.openssh.settings.PrintLastLog = "no";'
	);

	// click on "Deploy" button
	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await deployButton.click();

	// add the second VM to the deployment
	await page.locator('input').nth(2).locator('..').click();
	await page.locator('li').filter({ hasText: 'VM Test x64 2' }).click();

	// Click on new "Deploy" button in modal to confirm
	const deployButtonModal = page.getByRole('dialog').locator('button', { hasText: 'Deploy' });
	await deployButtonModal.click();

	// Wait for a fifth "completed" status
	await page.locator('td', { hasText: 'completed' }).nth(4).waitFor({ timeout: 360000 });

	// Navigate back to "Details" tab
	await page.locator('a', { hasText: 'Details' }).first().click();
	await page.locator('p', { hasText: 'Deployed:' }).first().waitFor();

	await waitForTerminalText(page, '[Hello World Custom Prompt]');

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 128
	});

	// Now, navigate to "Devices" page using sidebar and take a screenshot
	await page.locator('a', { hasText: 'Devices' }).locator('visible=true').first().click();

	// Wait for 2 "Connected" statuses
	await page.locator('td', { hasText: 'Connected' }).nth(1).waitFor({ timeout: 60000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 128
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
	test.setTimeout(360000);
	await page.waitForEvent('download');
});
