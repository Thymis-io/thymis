import { expect, test, type Locator, type Page } from '../playwright/fixtures';

type SavedConversation = {
	id: string;
	title: string;
	created_at: string;
	updated_at: string;
	message_count: number;
	messages: unknown[];
};

/** Fixed timestamp so mocked conversation metadata never changes mid-test. */
const TIMESTAMP = '2026-01-01T00:00:00.000Z';

const sseBody = (events: unknown[]) =>
	events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join('') + 'data: [DONE]\n\n';

const sse = (events: unknown[]) => ({
	contentType: 'text/event-stream',
	headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
	body: sseBody(events)
});

/**
 * Back the assistant's persisted-conversation endpoints with an in-memory store
 * so a spec starts from a known transcript.
 */
async function mockConversationStore(
	page: Page,
	saved: SavedConversation[] = []
): Promise<SavedConversation[]> {
	await page.route('**/api/agent/conversations', async (route) => {
		if (route.request().method() === 'POST') {
			const conversation: SavedConversation = {
				id: `conv_${saved.length + 1}`,
				title: 'New chat',
				created_at: TIMESTAMP,
				updated_at: TIMESTAMP,
				message_count: 0,
				messages: []
			};
			saved.unshift(conversation);
			await route.fulfill({ status: 201, json: conversation });
			return;
		}
		await route.fulfill({ json: saved });
	});
	await page.route('**/api/agent/conversations/*', async (route) => {
		const id = route.request().url().split('/').pop();
		const conversation = saved.find((candidate) => candidate.id === id);
		if (route.request().method() === 'DELETE') {
			const index = saved.findIndex((candidate) => candidate.id === id);
			if (index >= 0) saved.splice(index, 1);
			await route.fulfill({ status: 204 });
			return;
		}
		await route.fulfill(
			conversation
				? { json: conversation }
				: { status: 404, json: { detail: 'Conversation not found' } }
		);
	});
	return saved;
}

const openAssistant = async (page: Page) => {
	// The launcher is present in the server-rendered HTML before Svelte hydrates,
	// so wait for the page to settle before clicking it.
	await page.waitForLoadState('networkidle');
	const dialog = page.getByRole('dialog', { name: 'Thymis Assistant' });
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();
	await expect(dialog).toBeVisible();
	return dialog;
};

const sendPrompt = async (dialog: Locator, prompt: string) => {
	const input = dialog.getByRole('textbox', { name: 'Message Thymis Assistant' });
	await input.fill(prompt);
	await input.press('Enter');
};

test('opens and closes the floating Thymis Assistant', async ({ page }) => {
	await mockConversationStore(page);
	await page.goto('/overview');
	await page.waitForLoadState('networkidle');

	const launcher = page.getByRole('button', { name: 'Open Thymis Assistant' });
	await expect(launcher).toBeVisible();
	await launcher.click();

	const dialog = page.getByRole('dialog', { name: 'Thymis Assistant' });
	await expect(dialog).toBeVisible();
	await expect(dialog.getByRole('textbox', { name: 'Message Thymis Assistant' })).toBeVisible();
	await expect(
		dialog.getByRole('button', { name: 'Attach current VNC screenshot' })
	).toBeDisabled();
	await expect(dialog.getByText('Can inspect, change, and act on controller data')).toBeVisible();

	await dialog.getByRole('button', { name: 'Close Thymis Assistant' }).click();
	await expect(dialog).toBeHidden();
});

test('renders an AI SDK streamed response with Markdown and tool activity', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		expect(route.request().postDataJSON()).toMatchObject({
			conversation_id: 'conv_1',
			messages: [{ role: 'user', parts: [{ type: 'text', text: 'How is the fleet?' }] }]
		});
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_test' },
				{ type: 'start-step' },
				{ type: 'text-start', id: 'text_1' },
				{ type: 'text-delta', id: 'text_1', delta: '**Fleet** is healthy.' },
				{ type: 'text-end', id: 'text_1' },
				{
					type: 'tool-input-available',
					toolCallId: 'call_1',
					toolName: 'get_state',
					input: {},
					dynamic: true
				},
				{ type: 'tool-output-available', toolCallId: 'call_1', output: {} },
				{ type: 'text-start', id: 'text_2' },
				{ type: 'text-delta', id: 'text_2', delta: ' Current data loaded.' },
				{ type: 'text-end', id: 'text_2' },
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'How is the fleet?');

	await expect(dialog.getByText('How is the fleet?')).toBeVisible();
	await expect(dialog.getByText('Fleet is healthy.')).toBeVisible();
	await expect(dialog.locator('.assistant-markdown strong')).toHaveText('Fleet');
	await expect(dialog.getByText('get state', { exact: true })).toBeVisible();
	await expect(dialog.getByText('Current data loaded.')).toBeVisible();
	const assistantParts = dialog
		.locator('.assistant-message')
		.last()
		.locator('.assistant-message-content > *');
	await expect(assistantParts).toHaveCount(3);
	await expect(assistantParts.nth(0)).toContainText('Fleet is healthy.');
	await expect(assistantParts.nth(1)).toHaveText('get state');
	await expect(assistantParts.nth(2)).toContainText('Current data loaded.');
});

test('restores a saved conversation transcript when reopened', async ({ page }) => {
	await mockConversationStore(page, [
		{
			id: 'conv_saved',
			title: 'Earlier question',
			created_at: TIMESTAMP,
			updated_at: TIMESTAMP,
			message_count: 2,
			messages: [
				{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'Earlier question' }] },
				{
					id: 'a1',
					role: 'assistant',
					parts: [
						{ type: 'text', text: '**Earlier** answer.' },
						{
							type: 'dynamic-tool',
							toolCallId: 'call_old',
							toolName: 'navigate_frontend',
							state: 'output-available',
							input: { destination: 'tasks' },
							output: { destination: 'tasks', identifier: null }
						},
						{
							type: 'dynamic-tool',
							toolCallId: 'call_old_tool',
							toolName: 'get_fleet_alerts',
							state: 'output-available',
							input: {},
							output: {}
						},
						{
							type: 'data-entity-link',
							data: { entityType: 'task', identifier: 'task-9', label: 'build-9' }
						}
					]
				}
			]
		}
	]);
	await page.goto('/overview');
	const dialog = await openAssistant(page);

	await expect(dialog.getByText('Earlier question')).toBeVisible();
	await expect(dialog.locator('.assistant-markdown strong')).toHaveText('Earlier');
	await expect(dialog.getByText('get fleet alerts', { exact: true })).toBeVisible();
	await expect(dialog.getByRole('link', { name: 'build-9' })).toHaveAttribute(
		'href',
		'/tasks/task-9'
	);
	// A restored transcript must not replay the dashboard navigation it recorded.
	await expect(page).toHaveURL(/\/overview$/);
});

test('lists, switches, and deletes saved conversations', async ({ page }) => {
	const saved = await mockConversationStore(page, [
		{
			id: 'conv_newer',
			title: 'Newer question',
			created_at: TIMESTAMP,
			updated_at: TIMESTAMP,
			message_count: 2,
			messages: [
				{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'Newer question' }] },
				{ id: 'a1', role: 'assistant', parts: [{ type: 'text', text: 'Newer answer' }] }
			]
		},
		{
			id: 'conv_older',
			title: 'Older question',
			created_at: TIMESTAMP,
			updated_at: TIMESTAMP,
			message_count: 1,
			messages: [{ id: 'u2', role: 'user', parts: [{ type: 'text', text: 'Older question' }] }]
		}
	]);
	await page.goto('/overview');
	const dialog = await openAssistant(page);

	await expect(dialog.getByText('Newer answer')).toBeVisible();
	const historyToggle = dialog.getByRole('button', { name: 'Saved conversations' });
	await historyToggle.click();
	await expect(historyToggle).toHaveAttribute('aria-pressed', 'true');
	const history = dialog.locator('.assistant-history');
	await expect(history.getByText('Newer question')).toBeVisible();
	await expect(history.getByText('Older question')).toBeVisible();

	// Selecting a saved conversation replaces the transcript shown.
	await history.getByText('Older question').click();
	await expect(history).toBeHidden();
	await expect(dialog.getByText('Older question')).toBeVisible();

	// Deleting the active conversation clears the transcript but keeps the list open.
	await historyToggle.click();
	await history.getByRole('button', { name: 'Delete Older question' }).click();
	await expect(history.getByText('Older question')).toBeHidden();
	await expect(history.getByText('Newer question')).toBeVisible();
	await expect(historyToggle).toHaveAttribute('aria-pressed', 'true');

	// Deleting an inactive conversation leaves the empty transcript in place.
	await history.getByRole('button', { name: 'Delete Newer question' }).click();
	await expect(history.getByText('Newer question')).toBeHidden();
	await expect(
		history.getByText('No saved conversations yet. Send a message to start one.')
	).toBeVisible();
	expect(saved).toEqual([]);
});

test('renders an assistant entity link with its entity component', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_entity_link' },
				{ type: 'start-step' },
				{ type: 'text-start', id: 'text_entity' },
				{ type: 'text-delta', id: 'text_entity', delta: 'The image build is ready:' },
				{ type: 'text-end', id: 'text_entity' },
				{
					type: 'data-entity-link',
					data: { entityType: 'task', identifier: 'task-1', label: 'build-device-image' }
				},
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	await openAssistant(page);
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).fill('Show my image build');
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).press('Enter');

	const link = page.getByRole('link', { name: 'build-device-image' });
	await expect(link).toHaveAttribute('href', '/tasks/task-1');
	await expect(link.locator('svg')).toBeVisible();
});

test('executes dashboard navigation emitted by the assistant', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_navigation' },
				{ type: 'start-step' },
				{
					type: 'tool-input-available',
					toolCallId: 'call_navigation',
					toolName: 'navigate_frontend',
					input: { destination: 'tasks' },
					dynamic: true
				},
				{
					type: 'tool-output-available',
					toolCallId: 'call_navigation',
					output: { destination: 'tasks', identifier: null }
				},
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'Open my tasks');

	await expect(page).toHaveURL(/\/tasks$/);
});

test('does not navigate to an unknown assistant-provided route', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_invalid_navigation' },
				{ type: 'start-step' },
				{
					type: 'tool-input-available',
					toolCallId: 'call_invalid_navigation',
					toolName: 'navigate_frontend',
					input: { destination: 'not-a-route' },
					dynamic: true
				},
				{
					type: 'tool-output-available',
					toolCallId: 'call_invalid_navigation',
					output: {}
				},
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'Open an invalid route');

	await expect(page).toHaveURL(/\/overview$/);
});

test('keeps a long streamed reply in view', async ({ page }) => {
	const reply = Array.from({ length: 80 }, (_, index) => `Result line ${index + 1}`).join('\n');
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_scroll' },
				{ type: 'start-step' },
				{ type: 'text-start', id: 'text_scroll' },
				{ type: 'text-delta', id: 'text_scroll', delta: reply },
				{ type: 'text-end', id: 'text_scroll' },
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'Show a long reply');
	await expect(page.getByText('Result line 80')).toBeVisible();

	const messageScroll = page.locator('.assistant-messages');
	await expect
		.poll(() =>
			messageScroll.evaluate(
				(element) => element.scrollTop + element.clientHeight >= element.scrollHeight - 1
			)
		)
		.toBe(true);
});
