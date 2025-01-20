import { test, expect } from '../playwright/fixtures';
import { clearState, deleteAllTasks, expectPageToHaveScreenshotWithHighlight } from './utils';

test.describe.configure({ mode: 'serial' });

const colorSchemes = ['light', 'dark'] as const;

colorSchemes.forEach((colorScheme) => {
	test.describe(`Color scheme: ${colorScheme}`, () => {
		test.use({ colorScheme: colorScheme });

		test('overview page shows overview', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);

			await page.goto('/login');

			await page.fill('input[name="username"]', 'admin');
			await page.fill('input[name="password"]', 'testadminpassword');
			await page.click('button[type="submit"]');

			await page.waitForURL('http://localhost:8000/overview');

			await expect(page).toHaveScreenshot();
		});

		test('shows devices', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);
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
			console.log(`Is save button disabled? ${await saveButton.isDisabled()}`);
			await saveButton.click();

			await expect(page).toHaveScreenshot();

			// go to device details page, delete device
			const viewDetailsButton = page.locator('a', { hasText: 'View Details' }).first();
			await viewDetailsButton.click();

			await expect(page).toHaveScreenshot();

			const deleteButton = page.locator('button').filter({ hasText: 'Delete' });
			await deleteButton.click();

			await expect(page).toHaveScreenshot();

			const confirmButton = page.locator('button').filter({ hasText: 'Delete' }).nth(0);
			await confirmButton.click();

			await expect(page).toHaveScreenshot();

			const devicesNav = page.locator('a', { hasText: 'Devices' }).locator('visible=true').first();
			await devicesNav.click();

			await expect(page).toHaveScreenshot();
		});

		test('explores more pages', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);

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

		test('create whoami tag', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);

			// Navigate to the Tags page and create a new tag
			await page.goto('/tags');

			const addTagButton = page.locator('button').filter({ hasText: 'Create Tag' });
			await expectPageToHaveScreenshotWithHighlight(page, addTagButton);
			await addTagButton.click();

			await expect(page).toHaveScreenshot();

			const tagNameInput = page.locator('#display-name').first();
			await tagNameInput.fill('Who Am I');

			await expect(page).toHaveScreenshot();

			const saveButton = page.locator('button').filter({ hasText: 'Add tag' });
			await saveButton.click();

			// Configure the tag
			const configureTagButton = page
				.locator('a', { hasText: 'Configure Tag' })
				.locator('visible=true')
				.first();
			await expectPageToHaveScreenshotWithHighlight(page, configureTagButton);
			await configureTagButton.click();

			const addModuleButton = page.locator('#add-module').first();
			await expectPageToHaveScreenshotWithHighlight(page, addModuleButton.locator('svg').first());
			await addModuleButton.click();

			const addContainerModuleButton = page.locator('button').filter({ hasText: 'OCI Containers' });
			await expectPageToHaveScreenshotWithHighlight(page, addContainerModuleButton);
			await addContainerModuleButton.click();

			const containerModuleButton = page.locator('a').filter({ hasText: 'OCI Containers' });
			await containerModuleButton.click();

			await expect(page).toHaveScreenshot();

			const addContainerButton = page.locator('button').filter({ hasText: 'Add Container' });
			await expectPageToHaveScreenshotWithHighlight(page, addContainerButton);
			await addContainerButton.click();

			await expect(page).toHaveScreenshot();

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

			await expect(page).toHaveScreenshot();

			// Assign the tag
			await page.goto('/devices');

			await page.locator('button').filter({ hasText: 'Create New Device' }).click();
			await page.locator('#display-name').first().fill('Whoami Device');
			await page.locator('#device-type').first().selectOption({ label: 'Raspberry Pi 4' });
			await page.locator('button').filter({ hasText: 'Create device' }).click();

			const editTagButton = page
				.locator('tr')
				.filter({ hasText: 'Whoami Device' })
				.locator('button')
				.nth(1);
			await expectPageToHaveScreenshotWithHighlight(page, editTagButton);
			await editTagButton.click();

			await expect(page).toHaveScreenshot();

			await page.getByLabel('Device tags').click();
			await page.getByRole('option', { name: 'Who Am I' }).click();

			await expect(page).toHaveScreenshot();

			await page.getByRole('button', { name: 'Save' }).click();

			await expect(page).toHaveScreenshot();
		});

		test('Create update tasks', async ({ page, request }) => {
			await clearState(page, request);
			await deleteAllTasks(page, request);

			// Go to devices page
			await page.goto('/devices');

			// Click on "Update" button
			const updateButton = page.locator('button').filter({ hasText: 'Update' });
			await updateButton.click();

			// Expect a task to be created
			await expect(page).toHaveScreenshot({
				mask: [page.locator('.playwright-snapshot-unstable')]
			});
		});
	});
});
