import path from 'path';
import { test, expect, type Locator, type Page } from '../playwright/fixtures';

const checkoutRoot = path.resolve(process.cwd(), '..');
// The checkout running these tests: a `path:` URL, which the modal cannot split into fields.
const checkoutUrl = `path://${checkoutRoot}`;
// A commit on the main branch of Thymis-io/thymis-modules.
const thymisModulesCommit = '86f014412d9e500781e8418de86a6fef43bc1f65';
const refLabel = 'Branch / Tag / Full Commit SHA (optional)';

const removeRepositories = async (page: Page) => {
	const state = await (await page.request.get('/api/state')).json();
	state.repositories = {};
	await page.request.patch('/api/state', { data: state });
};

test.beforeEach(async ({ page }) => removeRepositories(page));
test.afterEach(async ({ page }) => removeRepositories(page));

const field = (dialog: Locator, label: string) =>
	dialog.locator(`div:has(> label:text-is("${label}"))`).locator('input, select').first();

const repositoryRow = (page: Page, name: string) =>
	page.locator('tr', { has: page.getByRole('button', { name, exact: true }) });

const openNewRepository = async (page: Page) => {
	await page.goto('/external-repositories');
	await page.getByRole('button', { name: 'Add Repository' }).click();
	const dialog = page.getByRole('dialog');
	await expect(dialog.getByRole('button', { name: 'Save' })).toBeVisible();
	return dialog;
};

const openRepository = async (page: Page, name: string) => {
	await repositoryRow(page, name).getByRole('button', { name, exact: true }).click();
	const dialog = page.getByRole('dialog');
	await expect(dialog.getByRole('button', { name: 'Save' })).toBeVisible();
	return dialog;
};

const save = async (dialog: Locator) => {
	await dialog.getByRole('button', { name: 'Save' }).click();
	await expect(dialog).toBeHidden();
};

const expectGitFields = async (
	dialog: Locator,
	fields: { protocol: string; host: string; owner: string; repo: string; ref: string }
) => {
	await expect(field(dialog, 'Type')).toHaveValue('git');
	await expect(field(dialog, 'Protocol')).toHaveValue(fields.protocol);
	await expect(field(dialog, 'Host')).toHaveValue(fields.host);
	await expect(field(dialog, 'Owner / Organization')).toHaveValue(fields.owner);
	await expect(field(dialog, 'Repository')).toHaveValue(fields.repo);
	await expect(field(dialog, refLabel)).toHaveValue(fields.ref);
};

const expectGithubFields = async (dialog: Locator, owner: string, repo: string) => {
	await expect(field(dialog, 'Type')).toHaveValue('github');
	await expect(field(dialog, 'Owner / Organization')).toHaveValue(owner);
	await expect(field(dialog, 'Repository')).toHaveValue(repo);
};

test('a local path repository is edited as a single URL field', async ({ page }) => {
	test.setTimeout(60_000);

	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('local-checkout');
	await field(dialog, 'Type').selectOption('raw');
	await field(dialog, 'Repository URL').fill(checkoutUrl);
	await save(dialog);

	const row = repositoryRow(page, 'local-checkout');
	await expect(row).toContainText(checkoutUrl);
	// The controller resolved the path: the checkout is found but is no module repository.
	await expect(row).toContainText('Not a Thymis Module Repository', { timeout: 45_000 });

	dialog = await openRepository(page, 'local-checkout');
	await expect(field(dialog, 'Type')).toHaveValue('raw');
	await expect(field(dialog, 'Repository URL')).toHaveValue(checkoutUrl);
	await expect(field(dialog, 'Host')).toHaveCount(0);
	await expect(field(dialog, 'Owner / Organization')).toHaveCount(0);

	await save(dialog);
	await expect(row).toContainText(checkoutUrl);
});

test('renaming a repository keeps its URL and reloads it under the new name', async ({ page }) => {
	test.setTimeout(60_000);

	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('local-checkout');
	await field(dialog, 'Type').selectOption('raw');
	await field(dialog, 'Repository URL').fill(checkoutUrl);
	await save(dialog);
	await expect(repositoryRow(page, 'local-checkout')).toContainText(checkoutUrl);

	dialog = await openRepository(page, 'local-checkout');
	await field(dialog, 'Repository Name').fill('renamed-checkout');
	await save(dialog);

	const row = repositoryRow(page, 'renamed-checkout');
	await expect(row).toContainText(checkoutUrl);
	await expect(repositoryRow(page, 'local-checkout')).toHaveCount(0);
	await expect(row).toContainText('Not a Thymis Module Repository', { timeout: 45_000 });

	await page.reload();
	await expect(repositoryRow(page, 'renamed-checkout')).toContainText(checkoutUrl);
	await expect(repositoryRow(page, 'local-checkout')).toHaveCount(0);
});

test('a GitHub repository keeps its fields when switching through Other', async ({ page }) => {
	test.setTimeout(60_000);

	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('thymis-modules');
	await field(dialog, 'Owner / Organization').fill('Thymis-io');
	await field(dialog, 'Repository').fill('thymis-modules');
	await save(dialog);

	const row = repositoryRow(page, 'thymis-modules');
	await expect(row).toContainText('github:Thymis-io/thymis-modules');
	await expect(row).toContainText(/Repo loaded with \d+ modules/, { timeout: 45_000 });

	dialog = await openRepository(page, 'thymis-modules');
	await expectGithubFields(dialog, 'Thymis-io', 'thymis-modules');

	await field(dialog, 'Type').selectOption('raw');
	await expect(field(dialog, 'Repository URL')).toHaveValue('github:Thymis-io/thymis-modules');
	await field(dialog, 'Type').selectOption('github');
	await expectGithubFields(dialog, 'Thymis-io', 'thymis-modules');

	await field(dialog, 'Type').selectOption('raw');
	await field(dialog, 'Repository URL').fill(
		'git+https://github.com/Thymis-io/thymis-modules.git?ref=main'
	);
	await field(dialog, 'Type').selectOption('git');
	const gitFields = {
		protocol: 'https',
		host: 'github.com',
		owner: 'Thymis-io',
		repo: 'thymis-modules',
		ref: 'main'
	};
	await expectGitFields(dialog, gitFields);

	await save(dialog);
	await expect(row).toContainText('git+https://github.com/Thymis-io/thymis-modules.git?ref=main');

	dialog = await openRepository(page, 'thymis-modules');
	await expectGitFields(dialog, gitFields);
});

test('leaving Other with an unparseable URL starts with empty fields', async ({ page }) => {
	const dialog = await openNewRepository(page);

	await field(dialog, 'Type').selectOption('raw');
	await field(dialog, 'Repository URL').fill(checkoutUrl);
	await field(dialog, 'Type').selectOption('github');

	await expectGithubFields(dialog, '', '');
});

test('the Git protocol decides between host fields and a directory path', async ({ page }) => {
	test.setTimeout(60_000);

	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('local-git');
	const compiledUrl = field(dialog, 'Compiled URL');

	// The new repository defaults to github:Thymis-io/thymis.
	await field(dialog, 'Type').selectOption('git');
	await expect(field(dialog, 'Protocol')).toHaveValue('https');
	await expect(field(dialog, 'Host')).toHaveValue('github.com');
	await expect(compiledUrl).toHaveValue('git+https://github.com/Thymis-io/thymis.git');

	await field(dialog, 'Protocol').selectOption('ssh');
	await expect(field(dialog, 'Host')).toHaveValue('git@github.com');
	await expect(compiledUrl).toHaveValue('git+ssh://git@github.com/Thymis-io/thymis.git');

	await field(dialog, 'Protocol').selectOption('https');
	await expect(field(dialog, 'Host')).toHaveValue('github.com');
	await expect(compiledUrl).toHaveValue('git+https://github.com/Thymis-io/thymis.git');

	await field(dialog, 'Protocol').selectOption('file');
	await expect(field(dialog, 'Host')).toHaveCount(0);
	await expect(field(dialog, 'Owner / Organization')).toHaveCount(0);
	await field(dialog, 'Absolute Directory Path').fill(checkoutRoot);
	await expect(compiledUrl).toHaveValue(`git+file://${checkoutRoot}`);
	await save(dialog);

	const row = repositoryRow(page, 'local-git');
	await expect(row).toContainText(`git+file://${checkoutRoot}`);
	await expect(row).toContainText('Not a Thymis Module Repository', { timeout: 45_000 });

	dialog = await openRepository(page, 'local-git');
	await expect(field(dialog, 'Type')).toHaveValue('git');
	await expect(field(dialog, 'Protocol')).toHaveValue('file');
	await expect(field(dialog, 'Absolute Directory Path')).toHaveValue(checkoutRoot);
});

test('a branch from the list or a commit SHA can be used as the ref', async ({ page }) => {
	test.setTimeout(60_000);

	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('modules-ref');
	await field(dialog, 'Repository').fill('thymis-modules');
	await dialog.getByRole('button', { name: 'Refresh Branches' }).click();
	await field(dialog, refLabel).click();
	await dialog.getByRole('option', { name: 'main', exact: true }).click();
	await expect(field(dialog, 'Compiled URL')).toHaveValue('github:Thymis-io/thymis-modules/main');
	await save(dialog);

	const row = repositoryRow(page, 'modules-ref');
	await expect(row).toContainText('github:Thymis-io/thymis-modules/main');

	dialog = await openRepository(page, 'modules-ref');
	await expect(field(dialog, refLabel)).toHaveValue('main');
	await field(dialog, refLabel).fill(thymisModulesCommit);
	await expect(field(dialog, 'Compiled URL')).toHaveValue(
		`github:Thymis-io/thymis-modules/${thymisModulesCommit}`
	);
	await save(dialog);
	await expect(row).toContainText(`github:Thymis-io/thymis-modules/${thymisModulesCommit}`);

	dialog = await openRepository(page, 'modules-ref');
	await expect(field(dialog, refLabel)).toHaveValue(thymisModulesCommit);
});

test('a GitLab repository reopens with its fields', async ({ page }) => {
	let dialog = await openNewRepository(page);
	await field(dialog, 'Repository Name').fill('veloren-rfcs');
	await field(dialog, 'Type').selectOption('gitlab');
	await field(dialog, 'Owner / Organization').fill('veloren');
	await field(dialog, 'Repository').fill('rfcs');
	await save(dialog);

	// veloren/rfcs has no flake.nix, so the controller cannot load it; only the round trip
	// through the modal and the parser is checked here.
	await expect(repositoryRow(page, 'veloren-rfcs')).toContainText('gitlab:veloren/rfcs');

	dialog = await openRepository(page, 'veloren-rfcs');
	await expect(field(dialog, 'Type')).toHaveValue('gitlab');
	await expect(field(dialog, 'Owner / Organization')).toHaveValue('veloren');
	await expect(field(dialog, 'Repository')).toHaveValue('rfcs');
});
