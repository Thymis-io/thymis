import { test, expect, type Page } from '../playwright/fixtures';
import { clearState, createConfiguration, createTag } from './utils';
import { listPages, detailPages, SEED } from './page-registry';

// Structure conformance: every page goes through the shared layout components
// (PageHead, DataTable + RowMenu, PageHead + Tabbar), which carry stable
// data-testid hooks. A page that doesn't use them lacks the hooks and fails here.
// This suite checks structure/navigation only — not content or business logic.

const createDeploymentInfo = async (page: Page, configId: string, host: string) => {
	await page.request.post('/api/create_deployment_info', {
		data: {
			deployed_config_id: configId,
			ssh_public_key: '',
			reachable_deployed_host: host
		}
	});
};

test.describe.configure({ mode: 'serial' });

// Seed once, first (serial mode guarantees order). Uses the authenticated page
// fixture so the shared backend state persists for the assertions below.
test('seed conformance data', async ({ page, request }) => {
	await clearState(page, request);
	await createConfiguration(page, SEED.configName, 'Raspberry Pi 4', []);
	await createTag(page, SEED.tagName);
	await createDeploymentInfo(page, SEED.configId, SEED.deviceHost);
});

for (const spec of listPages) {
	test(`list page "${spec.name}" follows the shared structure`, async ({ page }) => {
		await page.goto(spec.path);

		// Exactly one PageHead with a page title.
		const head = page.locator('[data-testid="page-head"]');
		await expect(head).toHaveCount(1);
		await expect(head.locator('h1.ds-page-title')).toHaveCount(1);

		// At least one DataTable (some pages, e.g. Devices, render more than one).
		const tables = page.locator('[data-testid="data-table"]');
		await expect(tables.first()).toBeVisible();

		// Every data row (across all tables) exposes a RowMenu trigger.
		const dataRows = page.locator(
			'[data-testid="data-table"] tbody tr:not(:has(td.ds-table-empty))'
		);
		const rowCount = await dataRows.count();
		if (rowCount > 0) {
			await expect(
				page.locator('[data-testid="data-table"] tbody button[aria-haspopup="menu"]')
			).toHaveCount(rowCount);
		}

		// The name link in the entity's row navigates to its detail/edit page.
		if (spec.nameLink) {
			const row = dataRows.filter({ hasText: spec.nameLink.rowText }).first();
			await row.getByRole('link').first().click();
			await expect(page).toHaveURL(spec.nameLink.urlPattern);
		}
	});
}

for (const spec of detailPages) {
	test(`detail page "${spec.name}" follows the shared structure`, async ({ page }) => {
		// Reach the detail page by opening the seeded entity from its list.
		await page.goto(spec.from.listPath);
		const row = page
			.locator('[data-testid="data-table"] tbody tr')
			.filter({ hasText: spec.from.rowText })
			.first();
		await row.getByRole('link').first().click();
		await expect(page).toHaveURL(spec.urlPattern);

		// Exactly one PageHead with a page title.
		await expect(page.locator('[data-testid="page-head"] h1.ds-page-title')).toHaveCount(1);

		// The shared Tabbar with the expected tabs in order (extra conditional tabs allowed).
		const tabbar = page.locator('[data-testid="tabbar"]');
		await expect(tabbar).toHaveCount(1);
		const tabLabels = (await tabbar.getByRole('tab').allInnerTexts()).map((s) => s.trim());
		const filtered = tabLabels.filter((label) => spec.expectedTabs.includes(label));
		expect(filtered).toEqual(spec.expectedTabs);

		// The primary action button lives in the PageHead.
		await expect(
			page.locator('[data-testid="page-head"]').getByRole('button', { name: spec.expectedAction })
		).toBeVisible();
	});
}
