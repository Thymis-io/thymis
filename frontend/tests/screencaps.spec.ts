import { test, expect, type Page } from '../playwright/fixtures';
import {
	clearState,
	createConfiguration,
	createTag,
	deleteAllTasks,
	expectScreenshot,
	expectScreenshotWithHighlight
} from './utils';

const createDeploymentInfo = async (
	page: Page,
	configId: string,
	sshPublicKey: string,
	host: string
) => {
	await page.request.post('/api/create_deployment_info', {
		data: {
			deployed_config_id: configId,
			ssh_public_key: sshPublicKey,
			reachable_deployed_host: host
		}
	});
};

const deleteDeploymentInfos = async (page: Page, configIds: string[]) => {
	for (const configId of configIds) {
		const deploymentInfos = await page.request.get(
			`/api/deployment_infos_by_config_id/${configId}`
		);

		for (const deploymentInfo of await deploymentInfos.json()) {
			await page.request.delete(`/api/deployment_info/${deploymentInfo.id}`);
		}
	}
};

test('overview page shows overview', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await page.locator('nav:visible').locator('a', { hasText: 'Overview' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('shows configuration', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// We can add Configurations
	const addConfigurationButton = page
		.locator('button')
		.filter({ hasText: 'Create New Configuration' });
	await addConfigurationButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	// select id display-name input and fill it with 'My Device 1'
	const displayNameInput = page.locator('#display-name').first();
	await displayNameInput.fill('My Device 1');

	const deviceTypeSelect = page.locator('#device-type').first();
	await deviceTypeSelect.selectOption({ label: 'Raspberry Pi 4' });

	const saveButton = page.locator('button').filter({ hasText: 'Create device configuration' });
	console.log(`Is save button disabled? ${await saveButton.isDisabled()}`);
	await saveButton.click();

	const viewDetailsButton = page.getByRole('button', { name: 'View Details' }).first();
	await viewDetailsButton.waitFor();

	await expectScreenshot(page, testInfo, screenshotCounter);

	// go to device details page, delete device
	await page.getByRole('button', { name: 'View Details' }).first().click();

	await page.waitForURL('/configuration/configuration-details*');

	await expectScreenshot(page, testInfo, screenshotCounter);

	const deleteButton = page.locator('button').filter({ hasText: 'Delete' });
	await deleteButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const confirmButton = page.locator('button').filter({ hasText: 'Delete' }).nth(0);
	await confirmButton.click();

	await page.locator('button').filter({ hasText: 'Create New Configuration' }).waitFor();
	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('explores more pages', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Navigate to the Devices page
	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Naviagte to hardware devices page
	await page.locator('nav:visible').locator('a', { hasText: 'Devices' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the Tags page
	await page.locator('nav:visible').locator('a', { hasText: 'Config-Tags' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the History page
	await page.locator('nav:visible').locator('a', { hasText: 'History' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the External Repositories page
	await page.locator('nav:visible').locator('a', { hasText: 'External Repositories' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the Secrets page
	await page.locator('nav:visible').locator('a', { hasText: 'Secrets' }).click();
	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('create whoami tag', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Navigate to the Tags page and create a new tag
	await page.locator('nav:visible').locator('a', { hasText: 'Config-Tags' }).click();

	const addTagButton = page.locator('button').filter({ hasText: 'Create Tag' });
	await expectScreenshotWithHighlight(page, addTagButton, testInfo, screenshotCounter);
	await addTagButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const tagNameInput = page.locator('#display-name').first();
	await tagNameInput.fill('Who Am I');

	await expectScreenshot(page, testInfo, screenshotCounter);

	const saveButton = page.locator('button').filter({ hasText: 'Add tag' });
	await saveButton.click();

	// Configure the tag
	const configureTagButton = page
		.locator('a', { hasText: 'Configure Tag' })
		.locator('visible=true')
		.first();
	await expectScreenshotWithHighlight(page, configureTagButton, testInfo, screenshotCounter);
	await configureTagButton.click();

	const addModuleButton = page.locator('#add-module').first();
	await expectScreenshotWithHighlight(
		page,
		addModuleButton.locator('svg').first(),
		testInfo,
		screenshotCounter
	);
	await addModuleButton.click();

	const addContainerModuleButton = page.locator('button').filter({ hasText: 'OCI Containers' });
	await expectScreenshotWithHighlight(page, addContainerModuleButton, testInfo, screenshotCounter);
	await addContainerModuleButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const addContainerButton = page.locator('button').filter({ hasText: 'Add Container' });
	await expectScreenshotWithHighlight(page, addContainerButton, testInfo, screenshotCounter);
	await addContainerButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const containerNameInput = page
		.locator('p', { hasText: 'Container Name' })
		.locator('..')
		.locator('input')
		.first();

	const containerImageInput = page
		.locator('p', { hasText: 'Image' })
		.locator('..')
		.locator('input')
		.first();

	await containerNameInput.fill('Whoami');
	await containerImageInput.fill('traefik/whoami');

	const portButton = page.locator('button').filter({ hasText: 'Add Port' });
	await portButton.click();

	const ports = page.locator('p', { hasText: 'Port' }).locator('..').locator('div');
	const hostPortInput = ports.locator('input').nth(0);
	const containerPortInput = ports.locator('input').nth(1);

	await hostPortInput.fill('80');
	await containerPortInput.fill('80');
	await containerPortInput.blur();

	// Assert the text values match what was entered
	expect(await containerNameInput.inputValue()).toBe('Whoami');
	expect(await containerImageInput.inputValue()).toBe('traefik/whoami');
	expect(await hostPortInput.inputValue()).toBe('80');
	expect(await containerPortInput.inputValue()).toBe('80');

	await expectScreenshot(page, testInfo, screenshotCounter);

	// Assign the tag
	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	await page.locator('button').filter({ hasText: 'Create New Configuration' }).click();
	await page.locator('#display-name').first().fill('Whoami Device');
	await page.locator('#device-type').first().selectOption({ label: 'Raspberry Pi 4' });
	await page.locator('button').filter({ hasText: 'Create device configuration' }).click();

	const editTagButton = page
		.locator('tr')
		.filter({ hasText: 'Whoami Device' })
		.locator('button')
		.nth(1);
	await expectScreenshotWithHighlight(page, editTagButton, testInfo, screenshotCounter);
	await editTagButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.getByLabel('Device tags').click();
	await page.getByRole('option', { name: 'Who Am I' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.getByRole('button', { name: 'Save' }).click();
	// wait for the modal to disappear
	await page.locator('tr').filter({ hasText: 'Who Am I' }).waitFor();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Create update tasks', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Go to devices page
	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	// Click on "Update" button
	const updateButton = page.locator('button').filter({ hasText: 'Update' });
	await updateButton.click();
	await updateButton.blur();

	await page.locator('td', { hasText: 'completed' }).first().waitFor();

	// Expect a task to be created
	await expectScreenshot(page, testInfo, screenshotCounter, {
		mask: [page.locator('.playwright-snapshot-unstable')]
	});
});

test('Create moneyshot', async ({ page, request, browser }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Create tags
	const tags = ['Display', 'Core', 'Location A', 'Location B'];
	for (const tag of tags) {
		await createTag(page, tag);
	}

	// Create devices
	const devices = [
		{ name: 'device01', tags: ['Display', 'Core', 'Location A'] },
		{ name: 'device02', tags: ['Display', 'Core', 'Location A'] },
		{ name: 'device03', tags: ['Display', 'Core', 'Location B'] },
		{ name: 'device04', tags: ['Core', 'Location B'] },
		{ name: 'device05', tags: ['Core', 'Location B'] }
	];
	for (const device of devices) {
		await createConfiguration(page, device.name, 'Raspberry Pi 4', device.tags);
	}

	// Go to configuration list
	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	// Create a update task as well as a project build task
	await page.locator('button').filter({ hasText: 'Update' }).click();

	await page.locator('td', { hasText: 'Update Nix Flake' }).first().waitFor();

	await page.locator('button').filter({ hasText: 'Build' }).click();

	// Take a screenshot

	// wait until: 2x on screen "completed"
	test.setTimeout(300000);
	await page.locator('td', { hasText: 'completed' }).nth(1).waitFor({ timeout: 300000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		mask: [page.locator('.playwright-snapshot-unstable')]
	});

	const updateSnapshots = testInfo.config.updateSnapshots;

	let maxDiffPixels = 1700;

	if (updateSnapshots === 'all' || updateSnapshots === 'changed') {
		maxDiffPixels = 100;
	}

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: maxDiffPixels,
		mask: []
	});

	const resolutions = [
		{ width: 1600, height: 900 },
		{ width: 1366, height: 768 },
		{ width: 1280, height: 720 },
		{ width: 1024, height: 768 },
		{ width: 800, height: 600 }
	];
	// create new browser context with viewport zoom
	for (const resolution of resolutions) {
		const zoomedContext = await browser.newContext({
			viewport: resolution
		});
		const zoomedPage = await zoomedContext.newPage();
		await zoomedPage.goto('/configuration/list');
		await expectScreenshot(zoomedPage, testInfo, screenshotCounter, {
			maxDiffPixels: maxDiffPixels,
			mask: []
		});
		await zoomedContext.close();
	}
});

test('Download Raspberry Pi 4 image', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Create a configuration
	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', []);

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	// find row with 'My Device 1' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'My Device 1' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	// find download button and click on it
	await page.locator('button').filter({ hasText: 'Download Device Image' }).first().click();
	await page
		.locator('button')
		.filter({ hasText: 'Commit & Download Device Image' })
		.first()
		.click();

	test.setTimeout(300000);
	await page.waitForEvent('download');
});

test('VNC View', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);
	await deleteDeploymentInfos(page, ['my-device-1', 'my-device-2', 'my-device-3', 'my-device-4']);

	await createTag(page, 'Display');
	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', ['Display']);
	await createConfiguration(page, 'My Device 2', 'Raspberry Pi 4', ['Display']);
	await createConfiguration(page, 'My Device 3', 'Raspberry Pi 4', ['Display']);
	await createConfiguration(page, 'My Device 4', 'Raspberry Pi 4', ['Display']);

	await createDeploymentInfo(page, 'my-device-1', '', '127.0.0.2');
	await createDeploymentInfo(page, 'my-device-2', '', '127.0.0.3');
	await createDeploymentInfo(page, 'my-device-3', '', '127.0.0.4');
	await createDeploymentInfo(page, 'my-device-4', '', '127.0.0.5');

	await page.locator('nav:visible').locator('a', { hasText: 'Config-Tags' }).click();

	// add Kiosk module with VNC server to tag
	const configureTagButton = page
		.locator('a', { hasText: 'Configure Tag' })
		.locator('visible=true')
		.first();
	await configureTagButton.click();

	const addModuleButton = page.locator('#add-module').first();
	await addModuleButton.click();

	const addKioskModuleButton = page.locator('button').filter({ hasText: 'Kiosk' });
	await addKioskModuleButton.click();

	const enableVNCButton = page
		.locator('p', { hasText: 'Enable VNC server' })
		.first()
		.locator('..')
		.locator('input')
		.locator('..');
	await enableVNCButton.click();

	await page.locator('nav:visible').locator('a', { hasText: 'VNC Devices' }).click();
	await page.locator('nav:visible').locator('a', { hasText: 'VNC Devices' }).click();
	await page.locator('nav:visible').locator('a', { hasText: 'VNC Devices' }).click();
	await page.locator('nav:visible').locator('a', { hasText: 'VNC Devices' }).click();
	await page.locator('nav:visible').locator('a', { hasText: 'VNC Devices' }).click();

	// wait for "Displays per Row"
	await page.getByText('Displays per Row:').waitFor();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.getByPlaceholder('Search...').click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('a').filter({ hasText: 'My Device 2' }).click();
	await page.locator('button').filter({ hasText: 'VNC' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Create History Entry', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', []);

	await page.locator('nav:visible').locator('a', { hasText: 'History' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Commit' }).click();

	await page.locator('div').filter({ hasText: '2 internal file changes' }).first().waitFor();

	const messageInput = page.getByPlaceholder('Summary of the changes');
	await messageInput.fill('Commiting changes');

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Commit' }).nth(1).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const showChangesButton = page.locator('button').filter({ hasText: 'Show Changes' }).nth(0);
	await showChangesButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Configure Wifi Network', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', []);

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	await page.getByRole('button', { name: 'View Details' }).click();

	await page.waitForURL('/configuration/configuration-details*');

	const configureTagButton = page.locator('a', { hasText: 'Configure' }).first();
	await configureTagButton.click();

	const wifiSSID = page.locator('p', { hasText: 'WiFi SSID' }).first();
	await wifiSSID.hover();
	await page.mouse.wheel(0, 400);

	await expectScreenshot(page, testInfo, screenshotCounter);

	const wifiSSIDInput = wifiSSID.locator('..').locator('input').first();
	await wifiSSIDInput.fill('MyWifi');

	const wifiPassword = page
		.locator('p', { hasText: 'WiFi Password' })
		.locator('..')
		.locator('input')
		.first();
	await wifiPassword.fill('MyPassword');

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Drag Taskbar', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await page.locator('nav:visible').locator('a', { hasText: 'Configs' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const taskbar = page.locator('#taskbar');
	const boundingBox = await taskbar.boundingBox();

	if (!boundingBox) {
		expect(boundingBox).not.toBeNull();
		return;
	}

	await page.mouse.move(boundingBox?.width / 2, boundingBox.y);
	await page.mouse.down();
	await page.mouse.move(boundingBox?.width / 2, boundingBox.y - 200);
	await page.mouse.up();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.getByTitle('Minimize Taskbar').first().click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.getByTitle('Show Taskbar').first().click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Create Secrets', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await page.locator('nav:visible').locator('a', { hasText: 'Secrets' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Create Secret' }).click();

	const secretName = page.locator('#secretName').first();
	const secretType = page.locator('#secretType').first();
	const secretProcessing = page.locator('#processingType').first();
	const includeInImage = page.locator('#includeInImage').first();

	await secretName.fill('My Secret 1');
	await secretType.selectOption({ label: 'Single Line' });
	await secretProcessing.selectOption({ label: 'Processing with mkpasswd yescrypt' });
	await includeInImage.check();
	await page.locator('#singleLineValue').first().fill('My Secret Value');
	await page.locator('#singleLineValue').first().blur();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Save' }).click();
	await page.locator('button').filter({ hasText: 'Create Secret' }).click();

	await secretName.fill('My Secret 2');
	await secretType.selectOption({ label: 'Multi Line' });
	await secretProcessing.selectOption({ label: 'No processing' });
	await page.locator('#multiLineValue').first().fill('Line 1\nLine 2\nLine 3');
	await page.locator('#multiLineValue').first().blur();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Save' }).click();
	await page.locator('button').filter({ hasText: 'Create Secret' }).click();

	await secretName.fill('My Secret 3');
	await secretType.selectOption({ label: 'List of environment variables' });

	await page.getByPlaceholder('KEY').nth(0).fill('KEY1');
	await page.getByPlaceholder('VALUE').nth(0).fill('Value');
	await page.locator('button').filter({ hasText: 'Add variable' }).click();
	await page.getByPlaceholder('KEY').nth(1).fill('KEY2');
	await page.getByPlaceholder('VALUE').nth(1).fill('Value');
	await page.locator('button').filter({ hasText: 'Add variable' }).click();
	await page.getByPlaceholder('KEY').nth(2).fill('KEY_TO_REMOVE');
	await page
		.locator('button')
		.filter({ has: page.locator('text="X"') })
		.nth(2)
		.click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	await page.locator('button').filter({ hasText: 'Save' }).click();
	await page.locator('button').filter({ hasText: 'Create Secret' }).click();

	await secretName.fill('My Secret 4');
	await secretType.selectOption({ label: 'File' });
	const fileInput = page.locator('#fileValue').first();
	await fileInput.setInputFiles({
		name: 'file.txt',
		mimeType: 'text/plain',
		buffer: Buffer.from('this is test')
	});

	await expectScreenshot(page, testInfo, screenshotCounter);
	await page.locator('button').filter({ hasText: 'Save' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('Open Deploy With Identical Config And Tag Identifier', async ({
	page,
	request
}, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Create a configuration
	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', []);

	// Create a tag with the same identifier as the configuration
	await createTag(page, 'My Device 1');

	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await deployButton.click();

	const searchbox = page.getByRole('searchbox').filter({ hasText: 'My Device 1' });
	await searchbox.click();
	await searchbox.getByText('My Device 1').nth(0).click();
	await searchbox.getByText('My Device 1').nth(1).click();

	await expectScreenshot(page, testInfo, screenshotCounter);
});
