import { test, expect, type Page } from '../playwright/fixtures';
import { clearState, createConfiguration, deleteAllTasks } from './utils';

const DEVICE_MODULE = 'thymis_controller.modules.thymis.ThymisDevice';

const persistedControllerUrl = async (page: Page) => {
	const response = await page.request.get('/api/state');
	const state = await response.json();
	const config = state.configs.find(
		(config: { identifier: string }) => config.identifier === 'validation-device'
	);
	return config?.modules.find((module: { type: string }) => module.type === DEVICE_MODULE)?.settings
		.agent_controller_url;
};

test('controller URL shows an error and is not saved while invalid', async ({ page, request }) => {
	await clearState(page, request);
	await deleteAllTasks(page, request);
	await createConfiguration(page, 'Validation Device', 'Raspberry Pi 4', []);

	await page
		.locator('tr')
		.filter({ hasText: 'Validation Device' })
		.getByRole('link', { name: 'Validation Device' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');
	await page.locator('a[href*="configuration/edit"]', { hasText: 'Device' }).first().click();

	const controllerUrlInput = page
		.locator('.ds-form-label', { hasText: 'Thymis Controller URL' })
		.locator('..')
		.locator('input');

	let statePatches = 0;
	page.on('request', (request) => {
		if (request.method() === 'PATCH' && new URL(request.url()).pathname === '/api/state') {
			statePatches += 1;
		}
	});

	await controllerUrlInput.fill('not a url');
	await controllerUrlInput.blur();

	await expect(
		page.getByText('Enter a valid URL starting with http://, https:// or file://')
	).toBeVisible();
	await expect(controllerUrlInput).toHaveAttribute('aria-invalid', 'true');
	await page.waitForTimeout(500);
	expect(statePatches).toBe(0);
	expect(await persistedControllerUrl(page)).not.toBe('not a url');

	const invalidState = await (await page.request.get('/api/state')).json();
	invalidState.configs
		.find((config: { identifier: string }) => config.identifier === 'validation-device')
		.modules.find(
			(module: { type: string }) => module.type === DEVICE_MODULE
		).settings.agent_controller_url = 'not a url';
	const rejected = await page.request.patch('/api/state', { data: invalidState });
	expect(rejected.status()).toBe(400);

	await controllerUrlInput.fill('https://controller.example.com');
	await controllerUrlInput.blur();
	await expect(controllerUrlInput).toHaveAttribute('aria-invalid', 'false');
	await expect.poll(() => persistedControllerUrl(page)).toBe('https://controller.example.com');

	await controllerUrlInput.fill('ftp://controller.example.com');
	await controllerUrlInput.blur();
	await expect(
		page.getByText('Enter a valid URL starting with http://, https:// or file://')
	).toBeVisible();
	await expect(controllerUrlInput).toHaveAttribute('aria-invalid', 'true');
	expect(await persistedControllerUrl(page)).toBe('https://controller.example.com');

	await controllerUrlInput.fill('file://var/image.png');
	await controllerUrlInput.blur();
	await expect(
		page.getByText('Use a full file path starting with /, e.g. file:///var/image.png')
	).toBeVisible();
	await expect(controllerUrlInput).toHaveAttribute('aria-invalid', 'true');
	expect(await persistedControllerUrl(page)).toBe('https://controller.example.com');
});
