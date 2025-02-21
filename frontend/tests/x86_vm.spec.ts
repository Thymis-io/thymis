import { test, expect, type Page } from '../playwright/fixtures';
import { clearState, deleteAllTasks } from './utils';
import * as os from 'os';

test.skip(os.arch() !== 'x64', 'You can only run this suite in an x86 VM');

const colorSchemes = ['light', 'dark'] as const;

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

colorSchemes.forEach((colorScheme) => {
	test.describe(`Color scheme: ${colorScheme}`, () => {
		test.use({ colorScheme: colorScheme });
		test('Create a x64 vm and run it', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);

			await createConfiguration(page, 'VM Test x64', 'Generic x86-64', []);

			await page.goto('/configuration/list');

			// find row with 'VM Test x64' and click on button 'View Details'
			await page
				.locator('tr')
				.filter({ hasText: 'VM Test x64' })
				.getByRole('button', { name: 'View Details' })
				.first()
				.click();

			// select button "Build and start VM"
			await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();

			// wait until: 1x on screen "completed", 1x on screen "running"
			test.setTimeout(360000);
			await page.locator('td', { hasText: 'completed' }).first().waitFor({ timeout: 360000 });
			await page.locator('td', { hasText: 'running' }).first().waitFor({ timeout: 30000 });

			// wait until "Deployed:" is shown on screen
			await page.locator('p', { hasText: 'Deployed:' }).first().waitFor({ timeout: 360000 });

			await expect(page).toHaveScreenshot({
				mask: [page.locator('.playwright-snapshot-unstable')]
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

			// Click on new "Deploy" button in modal to confirm
			const deployButtonModal = page.getByRole('dialog').locator('button', { hasText: 'Deploy' });
			await deployButtonModal.click();

			// Wait for a second "completed" status
			await page.locator('td', { hasText: 'completed' }).nth(1).waitFor({ timeout: 360000 });

			// Navigate back to "Details" tab
			await page.locator('a', { hasText: 'Details' }).first().click();

			await expect(page).toHaveScreenshot({
				mask: [page.locator('.playwright-snapshot-unstable')]
			});

			// Now, navigate to "Devices" page using sidebar and take a screenshot
			await page.locator('a', { hasText: 'Devices' }).locator('visible=true').first().click();

			await expect(page).toHaveScreenshot({
				mask: [page.locator('.playwright-snapshot-unstable')]
			});
		});
	});
});
