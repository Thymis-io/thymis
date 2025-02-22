import { test, expect, type Page } from '../playwright/fixtures';
import {
	clearState,
	deleteAllTasks,
	expectScreenshot,
	expectScreenshotWithHighlight
} from './utils';

const createConfiguration = async (
	page: Page,
	name: string,
	deviceType: string,
	tags: string[]
) => {
	await page.goto('/configuration/list');

	const addConfigurationButton = page
		.locator('button')
		.filter({ hasText: 'Create New Configuration' });
	await addConfigurationButton.click();

	const displayNameInput = page.locator('#display-name').first();
	await displayNameInput.fill(name);

	const deviceTypeSelect = page.locator('#device-type').first();
	await deviceTypeSelect.selectOption({ label: deviceType });

	if (tags.length > 0) {
		const tagsMultiSelect = page.locator('input[autocomplete]');
		await tagsMultiSelect.click();

		// for each tag, input and enter
		for (const tag of tags) {
			await page.getByRole('option', { name: tag }).click();
		}
	}

	await page.getByRole('heading', { name: 'Create a new device' }).click();

	const saveButton = page.locator('button').filter({ hasText: 'Create device configuration' });
	await saveButton.click();
};

const createTag = async (page: Page, name: string) => {
	await page.goto('/tags');

	const addTagButton = page.locator('button').filter({ hasText: 'Create Tag' });
	await addTagButton.click();

	const tagNameInput = page.locator('#display-name').first();
	await tagNameInput.fill(name);

	const saveButton = page.locator('button').filter({ hasText: 'Add tag' });
	await saveButton.click();
};

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

	await page.goto('/login');

	await page.fill('input[name="username"]', 'admin');
	await page.fill('input[name="password"]', 'testadminpassword');
	await page.click('button[type="submit"]');

	await page.waitForURL('http://localhost:8000/overview');

	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('shows configuration', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);
	const resp = await page.goto('/configuration/list');

	// 200 OK is expected
	expect(resp?.status()).toBe(200);
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

	await page.waitForURL('http://localhost:8000/configuration/configuration-details*');

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
	await page.goto('/configuration/list');
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Naviagte to hardware devices page
	await page.goto('/devices');
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the Tags page
	const tagsNav = page.locator('a', { hasText: 'Tags' }).locator('visible=true').first();
	await tagsNav.click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the History page
	const historyNav = page.locator('a', { hasText: 'History' }).locator('visible=true').first();
	await historyNav.click();
	await expectScreenshot(page, testInfo, screenshotCounter);

	// Navigate to the External Repositories page
	const externalReposNav = page
		.locator('a', { hasText: 'External Repositories' })
		.locator('visible=true')
		.first();
	await externalReposNav.click();
	await expectScreenshot(page, testInfo, screenshotCounter);
});

test('create whoami tag', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	// Navigate to the Tags page and create a new tag
	await page.goto('/tags');

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

	await page
		.locator('p', { hasText: 'Container Name' })
		.locator('..')
		.locator('input')
		.first()
		.fill('Whoami');
	await page
		.locator('p', { hasText: 'Image' })
		.locator('..')
		.locator('input')
		.first()
		.fill('traefik/whoami');
	const portButton = page.locator('button').filter({ hasText: 'Add Port' });
	await portButton.click();
	const ports = page.locator('p', { hasText: 'Port' }).locator('..').locator('div');
	await ports.locator('input').nth(0).fill('80');
	await ports.locator('input').nth(1).fill('80');
	await ports.locator('input').nth(1).blur();

	await expectScreenshot(page, testInfo, screenshotCounter);

	// Assign the tag
	await page.goto('/configuration/list');

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
	await page.goto('/configuration/list');

	// Click on "Update" button
	const updateButton = page.locator('button').filter({ hasText: 'Update' });
	await updateButton.click();

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
	await page.goto('/configuration/list');

	// Create a update task as well as a project build task
	await page.locator('button').filter({ hasText: 'Update' }).click();

	await page.locator('button').filter({ hasText: 'Build' }).click();

	// Take a screenshot

	// wait until: 2x on screen "completed"
	test.setTimeout(300000);
	await page.locator('td', { hasText: 'completed' }).nth(1).waitFor({ timeout: 300000 });

	await expectScreenshot(page, testInfo, screenshotCounter, {
		mask: [page.locator('.playwright-snapshot-unstable')]
	});

	await expectScreenshot(page, testInfo, screenshotCounter, {
		maxDiffPixels: 1000
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
		await zoomedPage.goto('http://localhost:8000/configuration/list');
		await expectScreenshot(zoomedPage, testInfo, screenshotCounter, {
			maxDiffPixels: 1000
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

	await page.goto('/configuration/list');

	// find row with 'My Device 1' and click on button 'View Details'
	await page
		.locator('tr')
		.filter({ hasText: 'My Device 1' })
		.getByRole('button', { name: 'View Details' })
		.first()
		.click();

	const downloadPromise = page.waitForEvent('download');

	// find download button and click on it
	await page.locator('button').filter({ hasText: 'Download Device Image' }).first().click();

	test.setTimeout(300000);
	await downloadPromise;
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

	await createDeploymentInfo(page, 'my-device-2', '', '127.0.0.2');
	await createDeploymentInfo(page, 'my-device-2', '', '127.0.0.3');
	await createDeploymentInfo(page, 'my-device-3', '', '127.0.0.4');
	await createDeploymentInfo(page, 'my-device-4', '', '127.0.0.5');

	await page.goto('/tags');

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

	await page.goto('/vnc');
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

	await page.goto('/history');

	await expectScreenshot(page, testInfo, screenshotCounter);

	const deployButtonAction = page.locator('button').filter({ hasText: 'Deploy' });
	await deployButtonAction.click();

	const messageInput = page.getByPlaceholder('Message');
	await messageInput.fill('Deploying device');

	await page.locator('input').nth(2).locator('..').click();
	await page.locator('li').filter({ hasText: 'My Device 1' }).click();

	await expectScreenshot(page, testInfo, screenshotCounter);

	const deployButton = page.locator('button').filter({ hasText: 'Deploy' }).nth(1);
	await deployButton.click();

	await page.locator('td', { hasText: 'completed' }).first().waitFor();

	await expectScreenshot(page, testInfo, screenshotCounter, {
		mask: [page.locator('.playwright-snapshot-unstable')]
	});

	const showChangesButton = page.locator('button').filter({ hasText: 'Show Changes' });
	await showChangesButton.click();

	await expectScreenshot(page, testInfo, screenshotCounter, {
		mask: [page.locator('.playwright-snapshot-unstable')]
	});
});

test('Configure Wifi Network', async ({ page, request }, testInfo) => {
	const screenshotCounter = { count: 0 };
	await clearState(page, request);
	await deleteAllTasks(page, request);

	await createConfiguration(page, 'My Device 1', 'Raspberry Pi 4', []);

	await page.goto('/configuration/list');

	await page.getByRole('button', { name: 'View Details' }).click();

	await page.waitForURL('http://localhost:8000/configuration/configuration-details*');

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
