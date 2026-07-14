import path from 'path';
import { test, expect, type Page, type Locator } from '../playwright/fixtures';
import { createConfiguration } from './utils';

// This spec captures fresh, real screenshots of the current UI for the
// hand-curated documentation pages under docs/src/lib/docs/reference/{ui,concepts}.
// It intentionally does not use toHaveScreenshot() visual-regression assertions;
// it writes the images directly into the docs tree.
const DOCS_ROOT = path.resolve(process.cwd(), '../docs/src/lib/docs/reference');
const UI_DIR = path.join(DOCS_ROOT, 'ui');
const CONCEPTS_DIR = path.join(DOCS_ROOT, 'concepts');
const DEVICE_LIFECYCLE_DIR = path.resolve(process.cwd(), '../docs/src/lib/docs/device-lifecycle');
const EXTERNAL_PROJECTS_DIR = path.resolve(process.cwd(), '../docs/src/lib/docs/external-projects');
const EXTERNAL_PROJECTS_MODULES_DIR = path.join(EXTERNAL_PROJECTS_DIR, 'thymis-modules');

/** Waits for SvelteKit's top navigation progress bar to finish and disappear,
 * so screenshots never catch it mid-animation. Safe to call even when no
 * navigation bar ever appeared (fast/no-op navigations). */
const waitForNavIdle = async (page: Page) => {
	const bar = page.locator('[role="progressbar"].svelte-progress-bar');
	await bar.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});
	await page.waitForTimeout(250);
};

/** Tight element screenshot (auto-crops to the element's own box). */
const shot = async (locator: Locator, filePath: string) => {
	await locator.scrollIntoViewIfNeeded();
	await waitForNavIdle(locator.page());
	await locator.screenshot({ path: filePath });
};

/** Screenshot a small margin around an element (matches the toolbar-button crop
 * style used throughout the existing docs, which shows a sliver of neighbours). */
const clipShot = async (page: Page, locator: Locator, filePath: string, margin = 36) => {
	await locator.scrollIntoViewIfNeeded();
	await locator.hover();
	await waitForNavIdle(page);
	const box = await locator.boundingBox();
	if (!box) throw new Error('element has no bounding box');
	const vp = page.viewportSize();
	const x = Math.max(0, box.x - margin);
	const y = Math.max(0, box.y - margin);
	const width = vp ? Math.min(vp.width - x, box.width + margin * 2) : box.width + margin * 2;
	const height = vp ? Math.min(vp.height - y, box.height + margin * 2) : box.height + margin * 2;
	await page.screenshot({ path: filePath, clip: { x, y, width, height } });
};

const contentArea = (page: Page) => page.locator('div.w-full.h-full.overflow-y-auto.p-4').first();

/** flowbite-svelte's role="dialog" is the full-viewport overlay; the visible
 * card is its role="document" body's parent Frame. Crop to that instead. */
const modalBox = (dialog: Locator) => dialog.locator('[role="document"]').locator('..');

/** Some modals put their submit button inside the flex-grown body instead of
 * Modal's dedicated footer slot; the body then stretches to fill the dialog's
 * centered height, leaving dead space below the real content. Crop to the
 * frame's top/left/width but stop just past `lastElement` instead of the
 * full (stretched) frame height. */
const modalShotTrimmed = async (
	page: Page,
	dialog: Locator,
	lastElement: Locator,
	filePath: string,
	margin = 16
) => {
	await waitForNavIdle(page);
	const frame = modalBox(dialog);
	const frameBox = await frame.boundingBox();
	const lastBox = await lastElement.boundingBox();
	if (!frameBox || !lastBox) throw new Error('modalShotTrimmed: missing bounding box');
	await page.screenshot({
		path: filePath,
		clip: {
			x: frameBox.x,
			y: frameBox.y,
			width: frameBox.width,
			height: Math.min(frameBox.height, lastBox.y + lastBox.height + margin - frameBox.y)
		}
	});
};

/** Full-viewport screenshot (matches the "whole app window" style used
 * throughout the device-lifecycle tutorials). */
const fullShot = async (page: Page, filePath: string) => {
	await waitForNavIdle(page);
	await page.screenshot({ path: filePath });
};

/** Draws a red callout box around an element (or elements), matching the
 * "here's where to click" highlight style used in the device-lifecycle docs. */
const highlight = async (page: Page, locators: Locator | Locator[], margin = 6) => {
	const list = Array.isArray(locators) ? locators : [locators];
	await waitForNavIdle(page);
	for (const locator of list) {
		await locator.scrollIntoViewIfNeeded();
		const box = await locator.boundingBox();
		if (!box) throw new Error('element has no bounding box to highlight');
		await page.evaluate(
			({ box, margin }) => {
				const div = document.createElement('div');
				div.className = 'docs-highlight-box';
				div.style.position = 'absolute';
				div.style.left = `${box.x - margin + window.scrollX}px`;
				div.style.top = `${box.y - margin + window.scrollY}px`;
				div.style.width = `${box.width + margin * 2}px`;
				div.style.height = `${box.height + margin * 2}px`;
				div.style.border = '3px solid #dc2626';
				div.style.borderRadius = '4px';
				div.style.zIndex = '999999';
				div.style.pointerEvents = 'none';
				document.body.appendChild(div);
			},
			{ box, margin }
		);
	}
};

const unhighlight = async (page: Page) => {
	await page.evaluate(() =>
		document.querySelectorAll('.docs-highlight-box').forEach((e) => e.remove())
	);
};

test('docs: toolbar buttons and commit dialogue', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Living Room Display', 'Raspberry Pi 4', []);
	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();

	const buildButton = page.locator('button').filter({ hasText: 'Build' });
	const updateButton = page.locator('button').filter({ hasText: 'Update' });
	const commitButton = page.locator('button').filter({ hasText: 'Commit' });
	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });

	await clipShot(page, buildButton, path.join(UI_DIR, 'build-button.png'));
	await clipShot(page, updateButton, path.join(UI_DIR, 'update-button.png'));
	await clipShot(page, commitButton, path.join(UI_DIR, 'commit-button.png'));
	await clipShot(page, deployButton, path.join(UI_DIR, 'deploy-button.png'));

	await commitButton.click();
	const dialog = page.getByRole('dialog');
	await dialog.getByText('Open Changes').waitFor();
	await shot(modalBox(dialog), path.join(UI_DIR, 'commit-dialogue.png'));
});

test('docs: tasks, build task, update task, task details', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Living Room Display', 'Raspberry Pi 4', []);
	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();

	await page.locator('button').filter({ hasText: 'Update' }).click();
	await page.locator('button').filter({ hasText: 'Build' }).click();

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Tasks' }).click();
	await page.waitForURL('/tasks*');
	const table = page.getByTestId('data-table');
	await table.locator('tbody tr').first().waitFor();
	// give both tasks a moment to report a running/queued state with a visible row
	await page.waitForTimeout(1500);

	await shot(table, path.join(UI_DIR, 'tasks.png'));

	const buildRow = table.locator('tbody tr').filter({ hasText: 'Build Project' }).first();
	await buildRow.waitFor();
	await clipShot(page, buildRow, path.join(UI_DIR, 'build-task.png'), 16);

	const updateRow = table.locator('tbody tr').filter({ hasText: 'Update Nix Flake' }).first();
	await updateRow.waitFor();
	await clipShot(page, updateRow, path.join(UI_DIR, 'update-task.png'), 16);

	await buildRow.locator('.task-name').click();
	await page.waitForURL('/tasks/*');
	await page.getByText('Submission Data').waitFor();
	await page.waitForTimeout(1000);
	await shot(contentArea(page), path.join(UI_DIR, 'task-details.png'));
});

test('docs: configure tab', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Living Room Display', 'Raspberry Pi 4', []);
	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page
		.locator('tr')
		.filter({ hasText: 'Living Room Display' })
		.getByRole('link', { name: 'Living Room Display' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');

	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');
	await page.locator('.ds-form-label', { hasText: 'Device Type' }).waitFor();

	await shot(contentArea(page), path.join(UI_DIR, 'configure-tab.png'));
});

test('docs: artifacts tab and artifact configuration', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	const artifactsNavItem = page
		.locator('nav.nav:visible a.nav-item')
		.filter({ hasText: 'Artifacts' });
	await clipShot(page, artifactsNavItem, path.join(CONCEPTS_DIR, 'artifacts-tab.png'), 20);

	await artifactsNavItem.click();
	await page.waitForURL('/artifacts*');
	await page.locator('button').filter({ hasText: 'Upload File' }).click();
	const fileInput = page.locator('input[type="file"]').first();
	await fileInput.setInputFiles({
		name: 'ssl-cert.pem',
		mimeType: 'text/plain',
		buffer: Buffer.from('-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----')
	});
	await page.getByRole('dialog').getByRole('button', { name: 'Upload File' }).click();
	await page.getByText('ssl-cert.pem').waitFor();

	await createConfiguration(page, 'Kiosk Display', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Kiosk Display' })
		.getByRole('link', { name: 'Kiosk Display' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');

	await page.locator('#add-module').first().click();
	await page.locator('button').filter({ hasText: 'Files' }).click();
	await page.waitForTimeout(300);

	await page.locator('button').filter({ hasText: 'Add Artifact' }).click();
	await page.locator('button').filter({ hasText: 'Add Artifact' }).scrollIntoViewIfNeeded();
	await page.locator("button:near(:text('Artifact')):text('Select an option')").click();
	await page.locator('option', { hasText: 'ssl-cert.pem' }).click();
	await page.getByRole('textbox', { name: 'Path' }).fill('/etc/ssl/certs/ssl-cert.pem');
	await page.getByRole('textbox', { name: 'Path' }).blur();

	const artifactsSetting = page.locator('label[for="config-artifacts"]').locator('..');
	await clipShot(
		page,
		artifactsSetting,
		path.join(CONCEPTS_DIR, 'artifacts-configuration.png'),
		24
	);
});

test('docs: tags', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Config-Tags' }).click();
	await page.waitForURL('/tags*');

	await page.locator('button').filter({ hasText: 'Create Tag' }).click();
	const createDialog = page.getByRole('dialog');
	await createDialog.locator('#display-name').fill('Digital Signage');
	await modalShotTrimmed(
		page,
		createDialog,
		createDialog.locator('button').filter({ hasText: 'Add tag' }),
		path.join(CONCEPTS_DIR, 'create-tag-modal.png')
	);
	await createDialog.locator('button').filter({ hasText: 'Add tag' }).click();

	await page
		.locator('tr')
		.filter({ hasText: 'Digital Signage' })
		.getByRole('link', { name: 'Digital Signage' })
		.first()
		.click({ force: true });
	await page.waitForURL('/configuration/edit*');
	await page.locator('#add-module').first().waitFor();

	const moduleCard = page.locator('.ds-card').first();
	await moduleCard.waitFor();
	const headBox = await page.getByRole('heading', { name: 'Digital Signage' }).boundingBox();
	const cardBox = await moduleCard.boundingBox();
	if (!headBox || !cardBox) throw new Error('tag page content not found');
	await page.screenshot({
		path: path.join(CONCEPTS_DIR, 'tag-page.png'),
		clip: {
			x: Math.max(0, headBox.x - 16),
			y: Math.max(0, headBox.y - 16),
			width: cardBox.x + cardBox.width + 24 - Math.max(0, headBox.x - 16),
			height: cardBox.y + cardBox.height + 24 - Math.max(0, headBox.y - 16)
		}
	});

	await createConfiguration(page, 'Foyer Sign', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Foyer Sign' })
		.getByRole('link', { name: 'Foyer Sign' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');

	const editTagsButton = page.getByRole('button', { name: 'Edit Tags' });
	await editTagsButton.click();
	const editDialog = page.getByRole('dialog');
	await page.getByLabel('Device tags').click();
	await page.getByRole('option', { name: 'Digital Signage' }).click();
	await modalShotTrimmed(
		page,
		editDialog,
		editDialog.getByRole('button', { name: 'Save' }),
		path.join(CONCEPTS_DIR, 'edit-tags-modal.png')
	);
});

test('docs: deploy modal and deployment tasks', async ({ page }) => {
	test.setTimeout(600000);
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Signage 01', 'Generic x86-64', []);
	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page
		.locator('tr')
		.filter({ hasText: 'Signage 01' })
		.getByRole('link', { name: 'Signage 01' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');

	// Boot a real local VM so this device shows up as a genuinely connected
	// deploy target (the deploy action only creates per-device tasks for
	// devices with a live agent connection).
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();
	await page.locator('div').filter({ hasText: 'internal file changes' }).first().waitFor();
	await page.locator('button').filter({ hasText: 'Commit & Build and start VM' }).first().click();

	// The commit flow occasionally races with the config-detail reload (the
	// image build silently no-ops if `selectedConfig` is momentarily
	// undefined right after commit) — retry via the direct-call path if no
	// build task shows up.
	await page.locator('nav.nav:visible').locator('a', { hasText: 'Tasks' }).click();
	await page.waitForURL('/tasks*');
	const buildTaskAppeared = await page
		.locator('tbody tr')
		.filter({ hasText: 'Build Image for Signage 01' })
		.first()
		.waitFor({ timeout: 10000 })
		.then(() => true)
		.catch(() => false);
	if (!buildTaskAppeared) {
		await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
		await page
			.locator('tr')
			.filter({ hasText: 'Signage 01' })
			.getByRole('link', { name: 'Signage 01' })
			.first()
			.click();
		await page.waitForURL('/configuration/configuration-details*');
		await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();
	}

	await page
		.locator('nav.nav:visible')
		.locator('a', { hasText: 'Devices', hasNotText: 'VNC Devices' })
		.click();
	await page.waitForURL('/devices/active*');
	await page.locator('td', { hasText: 'Connected' }).first().waitFor({ timeout: 480000 });

	// Give the device a friendly name so task rows read "Deploy to <name>"
	// instead of a raw UUID.
	await page
		.locator('tbody tr')
		.filter({ hasText: 'Signage 01' })
		.getByRole('link')
		.first()
		.click();
	await page.waitForURL('/devices/*/details*');
	await page.getByRole('button', { name: 'Rename' }).click();
	const renameDialog = page.getByRole('dialog');
	await renameDialog.getByPlaceholder('e.g. Display 1, Rack A').fill('Lobby Signage');
	await renameDialog.getByRole('button', { name: 'Save' }).click();
	await page.getByRole('heading', { name: 'Lobby Signage' }).waitFor();

	// Make a real config change so the deploy modal has something to deploy.
	await page.getByPlaceholder('Search...').click();
	await page.locator('#global-search-dropdown').getByRole('link', { name: 'Signage 01' }).click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');
	await page.locator('a[href*="configuration/edit"]', { hasText: 'Device' }).first().click();
	const hostnameInput = page
		.locator('.ds-form-label', { hasText: 'Default Hostname' })
		.locator('..')
		.locator('input');
	await hostnameInput.fill('signage-01-lobby');
	await hostnameInput.blur();

	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await deployButton.click();
	const deployDialog = page.getByRole('dialog');
	await deployDialog.getByText('Tags/configs/devices to deploy').waitFor();
	await deployDialog.locator('input[autocomplete]').click();
	await page.getByRole('option', { name: 'Signage 01', exact: true }).click();
	const deploySubmitButton = deployDialog
		.locator('button')
		.filter({ hasText: /^(Deploy|Commit & Deploy)$/ });
	await expect(deploySubmitButton).toBeEnabled({ timeout: 30000 });

	await shot(modalBox(deployDialog), path.join(UI_DIR, 'deploy-modal.png'));

	await deployDialog
		.locator('button')
		.filter({ hasText: /^(Deploy|Commit & Deploy)$/ })
		.click();

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Tasks' }).click();
	await page.waitForURL('/tasks*');
	const table = page.getByTestId('data-table');
	const deployRow = table.locator('tbody tr').filter({ hasText: 'Deploy to' }).first();
	await deployRow.waitFor({ timeout: 60000 });
	const parentRow = table.locator('tbody tr').filter({ hasText: 'Deploy Devices' }).first();
	await parentRow.waitFor();

	const parentBox = await parentRow.boundingBox();
	const childBox = await deployRow.boundingBox();
	if (!parentBox || !childBox) throw new Error('deployment task rows not found');
	const margin = 16;
	const top = Math.min(parentBox.y, childBox.y) - margin;
	const bottom = Math.max(parentBox.y + parentBox.height, childBox.y + childBox.height) + margin;
	await waitForNavIdle(page);
	await page.screenshot({
		path: path.join(UI_DIR, 'deployment-tasks.png'),
		clip: { x: 0, y: top, width: parentBox.x + parentBox.width, height: bottom - top }
	});
});

test('device-lifecycle: getting started', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page.waitForURL('/configuration/list*');
	const createButton = page.locator('button').filter({ hasText: 'Create New Configuration' });
	await highlight(page, createButton);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-initial-device-provisioning-1-linux.png')
	);
	await unhighlight(page);

	await createConfiguration(page, 'Test Configuration', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Test Configuration' })
		.getByRole('link', { name: 'Test Configuration' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');

	await page.locator('#add-module').first().click();
	await page.locator('button').filter({ hasText: 'Networking' }).click();
	await page.waitForTimeout(300);

	const ssidInput = page
		.locator('.ds-form-label', { hasText: 'WiFi SSID' })
		.locator('..')
		.locator('input');
	const passwordInput = page
		.locator('.ds-form-label', { hasText: 'WiFi Password' })
		.locator('..')
		.locator('input');
	await highlight(page, [ssidInput, passwordInput]);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-initial-device-provisioning-4-linux.png')
	);
	await unhighlight(page);

	await ssidInput.fill('MyHomeWifi');
	await passwordInput.fill('correct-horse-battery-staple');
	await passwordInput.blur();
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-initial-device-provisioning-5-linux.png')
	);

	const downloadButton = page.locator('button').filter({ hasText: 'Download Device Image' });
	await highlight(page, downloadButton);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-initial-device-provisioning-6-linux.png')
	);
	await unhighlight(page);
});

test('device-lifecycle: kiosk', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Kiosk Display', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Kiosk Display' })
		.getByRole('link', { name: 'Kiosk Display' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');

	await page.locator('#add-module').first().click();
	const kioskOption = page.locator('button').filter({ hasText: 'Kiosk' });
	await highlight(page, kioskOption);
	await shot(page.getByRole('dialog'), path.join(DEVICE_LIFECYCLE_DIR, 'add-kiosk-module.png'));
	await unhighlight(page);
	await kioskOption.click();
	await page.waitForTimeout(300);

	const urlInput = page
		.locator('.ds-form-label', { hasText: 'URL' })
		.locator('..')
		.locator('input');
	await urlInput.fill('https://thymis.io/');
	const vncToggle = page
		.locator('.ds-form-label', { hasText: 'Enable VNC server' })
		.locator('..')
		.locator('input')
		.locator('..');
	await vncToggle.click();
	await page.waitForTimeout(300);
	await page.setViewportSize({ width: 1920, height: 1400 });
	await contentArea(page).evaluate((el) => (el.scrollTop = 0));
	await shot(contentArea(page), path.join(DEVICE_LIFECYCLE_DIR, 'kiosk-configuration.png'));
	await page.setViewportSize({ width: 1920, height: 1080 });
});

test('device-lifecycle: secrets', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Secrets' }).click();
	await page.waitForURL('/secrets*');
	await page.locator('button').filter({ hasText: 'Create Secret' }).click();

	const dialog = page.getByRole('dialog');
	await dialog.locator('#secretName').fill('api-key');
	await dialog.locator('#singleLineValue').fill('sk_live_51H8x9qJ2eZv');
	await shot(modalBox(dialog), path.join(DEVICE_LIFECYCLE_DIR, 'secret-creation-form.png'));
});

test('device-lifecycle: tags', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Config-Tags' }).click();
	await page.waitForURL('/tags*');
	const createTagButton = page.locator('button').filter({ hasText: 'Create Tag' });
	await highlight(page, createTagButton);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'create-tag.png'));
	await unhighlight(page);

	await createTagButton.click();
	await page.locator('#display-name').first().fill('My Tag');
	await page.locator('button').filter({ hasText: 'Add tag' }).click();

	await createConfiguration(page, 'Camera', 'Raspberry Pi 4', []);
	await createConfiguration(page, 'Display', 'Raspberry Pi 4', []);

	await page
		.locator('tr')
		.filter({ hasText: 'Camera' })
		.getByRole('link', { name: 'Camera' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	const editTagsButton = page.getByRole('button', { name: 'Edit Tags' });
	await highlight(page, editTagsButton);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'assign-tag.png'));
	await unhighlight(page);

	await editTagsButton.click();
	await page.getByLabel('Device tags').click();
	await page.getByRole('option', { name: 'My Tag' }).click();
	await page.getByRole('dialog').getByRole('button', { name: 'Save' }).click();
	await page.getByRole('link', { name: 'My Tag' }).first().waitFor();

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page.waitForURL('/configuration/list*');
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'configs-with-tags.png'));

	await page
		.locator('tr')
		.filter({ hasText: 'My Tag' })
		.getByRole('link', { name: 'My Tag' })
		.first()
		.click({ force: true });
	await page.waitForURL('/configuration/edit*');
	const addModuleButton = page.locator('#add-module').first();
	await highlight(page, addModuleButton);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'add-module-to-tag.png'));
	await unhighlight(page);

	await addModuleButton.click();
	const deviceOption = page.locator('button').filter({ hasText: 'Device' }).first();
	await highlight(page, deviceOption);
	await shot(
		page.getByRole('dialog'),
		path.join(DEVICE_LIFECYCLE_DIR, 'add-core-device-configuration-module.png')
	);
	await unhighlight(page);
	await deviceOption.click();
	await page.waitForTimeout(300);

	await page.locator('#add-module').first().click();
	await page.locator('button').filter({ hasText: 'Networking' }).click();
	await page.waitForTimeout(300);

	const ssidField = page.locator('.ds-form-label', { hasText: 'WiFi SSID' }).locator('..');
	const passwordField = page.locator('.ds-form-label', { hasText: 'WiFi Password' }).locator('..');
	await ssidField.locator('input').fill('MyHomeWifi');
	await passwordField.locator('input').fill('correct-horse-battery-staple');
	await passwordField.locator('input').blur();
	const ssidClear = ssidField.locator('button').nth(2);
	const passwordClear = passwordField.locator('button').nth(2);
	await highlight(page, [ssidClear, passwordClear]);
	await shot(contentArea(page), path.join(DEVICE_LIFECYCLE_DIR, 'overwritten-setting.png'));
	await unhighlight(page);
});

test('device-lifecycle: update', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Test Configuration', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Test Configuration' })
		.getByRole('link', { name: 'Test Configuration' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');

	const updateButton = page.locator('button').filter({ hasText: 'Update' });
	await highlight(page, updateButton);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-deploy-update-1-linux.png')
	);
	await unhighlight(page);

	await updateButton.click();
	await page.locator('td', { hasText: 'Update Nix Flake' }).first().waitFor();

	const deployButton = page.locator('button').filter({ hasText: 'Deploy' });
	await highlight(page, deployButton);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-deploy-update-2-linux.png')
	);
	await unhighlight(page);

	await deployButton.click();
	const deployDialog = page.getByRole('dialog');
	await deployDialog.getByText('Tags/configs/devices to deploy').waitFor();
	const targetInput = deployDialog.locator('input[autocomplete]').locator('..');
	await highlight(page, targetInput);
	await fullShot(
		page,
		path.join(DEVICE_LIFECYCLE_DIR, 'Color-scheme-light-deploy-update-3-linux.png')
	);
	await unhighlight(page);
});

test('device-lifecycle: connected device', async ({ page }) => {
	test.setTimeout(600000);
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Koffer Device 01', 'Generic x86-64', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Koffer Device 01' })
		.getByRole('link', { name: 'Koffer Device 01' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');

	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');
	await page.locator('#add-module').first().click();
	await page.locator('button').filter({ hasText: 'Kiosk' }).click();
	await page.waitForTimeout(300);
	const urlInput = page
		.locator('.ds-form-label', { hasText: 'URL' })
		.locator('..')
		.locator('input');
	await urlInput.fill('https://thymis.io/');
	const vncToggle = page
		.locator('.ds-form-label', { hasText: 'Enable VNC server' })
		.locator('..')
		.locator('input')
		.locator('..');
	await vncToggle.click();
	await page.waitForTimeout(300);

	await page.getByRole('tab', { name: 'Details' }).click();
	await page.waitForURL('/configuration/configuration-details*');

	// Boot a real local VM so this device shows up as genuinely connected.
	await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();
	await page.locator('div').filter({ hasText: 'internal file changes' }).first().waitFor();
	await page.locator('button').filter({ hasText: 'Commit & Build and start VM' }).first().click();

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Tasks' }).click();
	await page.waitForURL('/tasks*');
	const buildTaskAppeared = await page
		.locator('tbody tr')
		.filter({ hasText: 'Build Image for Koffer Device 01' })
		.first()
		.waitFor({ timeout: 10000 })
		.then(() => true)
		.catch(() => false);
	if (!buildTaskAppeared) {
		await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
		await page
			.locator('tr')
			.filter({ hasText: 'Koffer Device 01' })
			.getByRole('link', { name: 'Koffer Device 01' })
			.first()
			.click();
		await page.waitForURL('/configuration/configuration-details*');
		await page.locator('button').filter({ hasText: 'Build and start VM' }).first().click();
	}

	await page
		.locator('nav.nav:visible')
		.locator('a', { hasText: 'Devices', hasNotText: 'VNC Devices' })
		.click();
	await page.waitForURL('/devices/active*');
	await page.locator('td', { hasText: 'Connected' }).first().waitFor({ timeout: 480000 });

	await page
		.locator('tbody tr')
		.filter({ hasText: 'Koffer Device 01' })
		.getByRole('link')
		.first()
		.click();
	await page.waitForURL('/devices/*/details*');
	await page.getByText('Online').first().waitFor({ timeout: 60000 });
	await page.waitForTimeout(2000);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'device-deployed.png'));

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Configs' }).click();
	await page.waitForURL('/configuration/list*');
	await page
		.locator('tr')
		.filter({ hasText: 'Koffer Device 01' })
		.getByRole('link', { name: 'Koffer Device 01' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Terminal' }).click();
	await page.waitForURL('/configuration/terminal*');
	await page.locator('.xterm-helper-textarea').first().waitFor({ timeout: 30000 });
	await page.waitForTimeout(4000);
	await page.locator('.xterm-helper-textarea').first().click();
	await page.keyboard.press('Enter');
	await page.waitForTimeout(3000);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'terminal-sessions.png'));

	await page
		.locator('nav.nav:visible')
		.locator('a', { hasText: 'Devices', hasNotText: 'VNC Devices' })
		.click();
	await page.waitForURL('/devices/active*');
	await page
		.locator('tbody tr')
		.filter({ hasText: 'Koffer Device 01' })
		.getByRole('link')
		.first()
		.click();
	await page.waitForURL('/devices/*/details*');
	await page.locator('button').filter({ hasText: 'VNC', hasNotText: 'VNC Devices' }).click();
	await page.waitForURL('/devices/*/vnc*');
	await page.getByLabel('Control Device').waitFor({ timeout: 30000 });
	await page.waitForTimeout(5000);
	await page.getByLabel('Control Device').hover();
	await page.waitForTimeout(500);
	await fullShot(page, path.join(DEVICE_LIFECYCLE_DIR, 'vnc-control.png'));
});

test('external-projects: repositories and device type', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'x86 Device', 'Generic x86-64', []);
	await page
		.locator('tr')
		.filter({ hasText: 'x86 Device' })
		.getByRole('link', { name: 'x86 Device' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');
	await page.locator('.ds-form-label', { hasText: 'Device Type' }).waitFor();
	await shot(contentArea(page), path.join(EXTERNAL_PROJECTS_DIR, 'select_generic_device_type.png'));

	await page.locator('nav.nav:visible').locator('a', { hasText: 'Secrets' }).click();
	await page.waitForURL('/secrets*');
	await page.locator('button').filter({ hasText: 'Create Secret' }).click();
	let dialog = page.getByRole('dialog');
	await dialog.locator('#secretName').fill('github key');
	await dialog.locator('#singleLineValue').fill('ghp_rmV2grm4AWzfG87bIZTfoH5MNzDeCT4CGUrF');
	await dialog.locator('button').filter({ hasText: 'Save' }).click();
	await page.getByText('github key').first().waitFor();

	await page.locator('button').filter({ hasText: 'Create Secret' }).click();
	dialog = page.getByRole('dialog');
	await dialog.locator('#secretName').fill('gitlab token');
	await dialog.locator('#singleLineValue').fill('glpat-8x9qJ2eZvH8x9qJ2eZv');
	await dialog.locator('button').filter({ hasText: 'Save' }).click();
	await page.getByText('gitlab token').first().waitFor();
	await fullShot(page, path.join(EXTERNAL_PROJECTS_DIR, 'api-key-secret.png'));

	await page.locator('nav.nav:visible').locator('a', { hasText: 'External Repositories' }).click();
	await page.waitForURL('/external-repositories*');
	await page.locator('button').filter({ hasText: 'Add Repository' }).click();
	const repoDialog = page.getByRole('dialog');
	await repoDialog.getByRole('button', { name: 'Save' }).waitFor();

	const secretSelect = repoDialog
		.locator('label', { hasText: 'API Key Secret' })
		.locator('..')
		.locator('select');
	await secretSelect.selectOption({ label: 'github key (single_line)' });
	await highlight(page, secretSelect);
	await shot(
		modalBox(repoDialog),
		path.join(EXTERNAL_PROJECTS_DIR, 'add-external-repo-with-api-key.png')
	);
	await unhighlight(page);

	await repoDialog.getByRole('button', { name: 'Save' }).click();
	await page.locator('table').getByText('thymis').first().waitFor();
	await fullShot(page, path.join(EXTERNAL_PROJECTS_DIR, 'external-repo-screenshot.png'));
});

test('external-projects: oci and custom nix modules', async ({ page }) => {
	await page.goto('/overview', { waitUntil: 'networkidle' });

	await createConfiguration(page, 'Docs Device', 'Raspberry Pi 4', []);
	await page
		.locator('tr')
		.filter({ hasText: 'Docs Device' })
		.getByRole('link', { name: 'Docs Device' })
		.first()
		.click();
	await page.waitForURL('/configuration/configuration-details*');
	await page.getByRole('tab', { name: 'Configure' }).click();
	await page.waitForURL('/configuration/edit*');

	await page.locator('#add-module').first().click();
	await page.locator('button').filter({ hasText: 'OCI Containers' }).click();
	await page.waitForTimeout(300);
	await page.locator('button').filter({ hasText: 'Add Container' }).click();
	await page.waitForTimeout(300);
	await shot(contentArea(page), path.join(EXTERNAL_PROJECTS_DIR, 'oci-containers.png'));

	await page.locator('#add-module').first().click();
	const customNixOption = page.locator('button').filter({ hasText: 'Custom Nix' });
	await highlight(page, customNixOption);
	await shot(
		page.getByRole('dialog'),
		path.join(EXTERNAL_PROJECTS_MODULES_DIR, 'add-custom-module.png')
	);
	await unhighlight(page);
	await customNixOption.click();
	await page.waitForTimeout(300);
	await page.locator('.monaco-editor').first().waitFor();
	await page.waitForTimeout(500);
	await shot(
		contentArea(page),
		path.join(EXTERNAL_PROJECTS_MODULES_DIR, 'custom-module-configuration.png')
	);

	const editor = page.locator('.monaco-editor').first();
	await editor.click();
	await page.keyboard.press('Control+a');
	await page.keyboard.press('Delete');
	await page.keyboard.insertText(
		'{ pkgs, ... }:\n{\n  environment.systemPackages = with pkgs; [ vim ];\n}'
	);
	await page.keyboard.press('Control+End');
	await page.keyboard.press('Shift+Tab');
	await page.waitForTimeout(500);
	await shot(
		contentArea(page),
		path.join(EXTERNAL_PROJECTS_MODULES_DIR, 'custom-module-example.png')
	);
	await shot(contentArea(page), path.join(EXTERNAL_PROJECTS_DIR, 'custom-thymis-module.png'));
});
