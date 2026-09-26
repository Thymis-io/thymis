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

/** 1x1 PNG, so a rendered attachment must actually decode in the browser. */
const ONE_PIXEL_PNG =
	'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC';

const sseBody = (events: unknown[]) =>
	events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join('') + 'data: [DONE]\n\n';

const sse = (events: unknown[]) => ({
	contentType: 'text/event-stream',
	headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
	body: sseBody(events)
});

const textStream = (messageId: string, text: string) => [
	{ type: 'start', messageId },
	{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
	{ type: 'start-step' },
	{ type: 'text-start', id: `${messageId}-text` },
	{ type: 'text-delta', id: `${messageId}-text`, delta: text },
	{ type: 'text-end', id: `${messageId}-text` },
	{ type: 'finish-step' },
	{ type: 'finish', finishReason: 'stop' }
];

/**
 * Back the assistant's persisted-conversation endpoints with an in-memory store
 * so a spec starts from a known transcript.
 */
async function mockConversationStore(
	page: Page,
	saved: SavedConversation[] = []
): Promise<SavedConversation[]> {
	await page.route('**/api/agent/conversations*', async (route) => {
		const request = route.request();
		if (request.method() === 'POST') {
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
		const query = new URL(request.url()).searchParams.get('q');
		await route.fulfill({
			json: query ? saved.filter((item) => item.title.includes(query)) : saved
		});
	});
	await page.route('**/api/agent/conversations/*', async (route) => {
		const request = route.request();
		const url = new URL(request.url());
		const id = url.pathname.split('/').pop();
		const conversation = saved.find((candidate) => candidate.id === id);
		if (request.method() === 'DELETE') {
			const index = saved.findIndex((candidate) => candidate.id === id);
			if (index >= 0) saved.splice(index, 1);
			await route.fulfill({ status: 204 });
			return;
		}
		if (request.method() === 'PATCH') {
			if (!conversation) {
				await route.fulfill({ status: 404, json: { detail: 'Conversation not found' } });
				return;
			}
			conversation.title = request.postDataJSON().title;
			await route.fulfill({ json: conversation });
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

test('closes the assistant with Escape and restores launcher focus', async ({ page }) => {
	await mockConversationStore(page);
	await page.goto('/overview');
	const dialog = await openAssistant(page);

	await dialog.getByRole('textbox', { name: 'Message Thymis Assistant' }).press('Escape');

	await expect(dialog).toBeHidden();
	await expect(page.getByRole('button', { name: 'Open Thymis Assistant' })).toBeFocused();
});

test('renders an AI SDK streamed response with Markdown and tool activity', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		expect(route.request().postDataJSON()).toMatchObject({
			conversation_id: 'conv_1',
			trigger: 'submit-message',
			messages: [{ role: 'user', parts: [{ type: 'text', text: 'How is the fleet?' }] }]
		});
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_test' },
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
				{ type: 'start-step' },
				{ type: 'reasoning-start', id: 'reasoning_1' },
				{ type: 'reasoning-delta', id: 'reasoning_1', delta: 'Checking the fleet first.' },
				{ type: 'reasoning-end', id: 'reasoning_1' },
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
				{
					type: 'tool-output-available',
					toolCallId: 'call_1',
					output: { devices: 0, connected: 0 }
				},
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
		.locator('.assistant-markdown > *');
	await expect(assistantParts).toHaveCount(2);
	await expect(assistantParts.nth(0)).toContainText('Fleet is healthy.');
	await expect(assistantParts.nth(1)).toContainText('Current data loaded.');

	// The turn is time-stamped from the streamed message metadata.
	await expect(dialog.locator('.assistant-message time').last()).toHaveAttribute(
		'datetime',
		TIMESTAMP
	);
	// The reply can be copied.
	await expect(dialog.getByRole('button', { name: 'Copy response' }).last()).toBeVisible();
});

test('shows a tool call whose arguments and result expand', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_tool' },
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
				{ type: 'start-step' },
				{
					type: 'tool-input-available',
					toolCallId: 'call_fleet',
					toolName: 'get_fleet_connectivity',
					input: { hours: 24 },
					dynamic: true
				},
				{
					type: 'tool-output-available',
					toolCallId: 'call_fleet',
					output: { connected: 0, offline: 3 }
				},
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'How is the fleet?');

	const tool = dialog.locator('.assistant-tool');
	await expect(tool).toContainText('get fleet connectivity');
	// Collapsed until the operator asks for the details.
	await expect(tool.locator('.assistant-tool-block').first()).toBeHidden();

	await tool.locator('summary').click();
	await expect(tool.getByText('Arguments')).toBeVisible();
	await expect(tool.getByText('Result')).toBeVisible();
	await expect(tool.locator('pre').first()).toContainText('"hours": 24');
	await expect(tool.locator('pre').last()).toContainText('"offline": 3');
});

test('shows model thinking in a collapsed block', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_thinking' },
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
				{ type: 'start-step' },
				{ type: 'reasoning-start', id: 'reasoning_1' },
				{
					type: 'reasoning-delta',
					id: 'reasoning_1',
					delta: 'The operator asked about the fleet, so I should call get_state.'
				},
				{ type: 'reasoning-end', id: 'reasoning_1' },
				{ type: 'text-start', id: 'text_1' },
				{ type: 'text-delta', id: 'text_1', delta: 'Nothing is connected.' },
				{ type: 'text-end', id: 'text_1' },
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'How is the fleet?');

	const reasoning = dialog.locator('.assistant-reasoning');
	await expect(reasoning.locator('summary')).toHaveText('Thinking');
	await expect(reasoning.locator('pre')).toBeHidden();
	await expect(dialog.getByText('Nothing is connected.')).toBeVisible();

	await reasoning.locator('summary').click();
	await expect(reasoning.locator('pre')).toContainText('so I should call get_state');
});

test('copies a response and regenerates the last answer', async ({ page }) => {
	await mockConversationStore(page);
	let replies = 0;
	await page.route('**/api/agent/chat', async (route) => {
		replies += 1;
		if (replies > 1) {
			expect(route.request().postDataJSON()).toMatchObject({
				trigger: 'regenerate-message'
			});
		}
		await route.fulfill(
			sse(textStream(`msg_${replies}`, replies > 1 ? 'Second answer.' : 'First answer.'))
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'How is the fleet?');
	await expect(dialog.getByText('First answer.')).toBeVisible();

	await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
	await dialog.getByRole('button', { name: 'Copy response' }).last().click();
	expect(await page.evaluate(() => navigator.clipboard.readText())).toContain('First answer.');

	await dialog.getByRole('button', { name: 'Regenerate response' }).click();
	await expect(dialog.getByText('Second answer.')).toBeVisible();
	await expect(dialog.getByText('First answer.')).toBeHidden();
});

test('renders fenced code blocks with a copy button', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_code' },
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
				{ type: 'start-step' },
				{ type: 'text-start', id: 'text_code' },
				{
					type: 'text-delta',
					id: 'text_code',
					delta: 'Run this:\n\n```sh\nsystemctl restart display-manager\n```\n'
				},
				{ type: 'text-end', id: 'text_code' },
				{ type: 'finish-step' },
				{ type: 'finish', finishReason: 'stop' }
			])
		);
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'Show the command');

	await expect(dialog.getByText('Run this:')).toBeVisible();
	await expect(dialog.getByText('systemctl restart display-manager')).toBeVisible();
	await expect(dialog.getByRole('button', { name: 'Copy', exact: true })).toBeVisible();
});

test('restores a saved conversation transcript when reopened', async ({ page }) => {
	await page.route('**/api/agent/files/*', (route) =>
		route.fulfill({
			contentType: 'image/png',
			body: Buffer.from(ONE_PIXEL_PNG, 'base64')
		})
	);
	await mockConversationStore(page, [
		{
			id: 'conv_saved',
			title: 'Earlier question',
			created_at: TIMESTAMP,
			updated_at: TIMESTAMP,
			message_count: 2,
			messages: [
				{
					id: 'u1',
					role: 'user',
					parts: [
						{ type: 'text', text: 'Earlier question' },
						{
							type: 'file',
							mediaType: 'image/png',
							filename: 'vnc-device.png',
							url: '/api/agent/files/file_1'
						}
					],
					metadata: { createdAt: TIMESTAMP }
				},
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
					],
					metadata: { createdAt: TIMESTAMP }
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
	const attachment = dialog.locator('.assistant-attachment');
	await expect(attachment).toHaveAttribute('src', '/api/agent/files/file_1');
	await expect
		.poll(() => attachment.evaluate((element) => (element as HTMLImageElement).naturalWidth))
		.toBeGreaterThan(0);
	// A restored transcript must not replay the dashboard navigation it recorded.
	await expect(page).toHaveURL(/\/overview$/);
});

test('lists, searches, renames, and deletes saved conversations', async ({ page }) => {
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

	// Searching asks the controller for matching titles.
	const search = history.getByRole('searchbox', { name: 'Search conversations...' });
	await search.fill('Older');
	await expect(history.getByText('Older question')).toBeVisible();
	await expect(history.getByText('Newer question')).toBeHidden();
	await search.fill('');

	// Renaming replaces the stored title.
	await history.getByRole('button', { name: 'Rename conversation' }).first().click();
	const renameField = history.getByRole('textbox', { name: 'Rename conversation' });
	await renameField.fill('Renamed conversation');
	await renameField.press('Enter');
	await expect(history.getByText('Renamed conversation')).toBeVisible();
	expect(saved[0].title).toBe('Renamed conversation');

	// Selecting a saved conversation replaces the transcript shown.
	await history.getByText('Older question').click();
	await expect(history).toBeHidden();
	await expect(dialog.getByText('Older question')).toBeVisible();

	// Deleting the active conversation clears the transcript but keeps the list open.
	await historyToggle.click();
	await history.getByRole('button', { name: 'Delete Older question' }).click();
	await expect(history.getByText('Older question')).toBeHidden();
	await expect(history.getByText('Renamed conversation')).toBeVisible();
	await expect(historyToggle).toHaveAttribute('aria-pressed', 'true');

	await history.getByRole('button', { name: 'Delete Renamed conversation' }).click();
	await expect(
		history.getByText('No saved conversations yet. Send a message to start one.')
	).toBeVisible();
	expect(saved).toEqual([]);
});

test('downloads the active conversation as Markdown', async ({ page }) => {
	await page.route('**/api/agent/files/*', (route) =>
		route.fulfill({
			contentType: 'image/png',
			body: Buffer.from(ONE_PIXEL_PNG, 'base64')
		})
	);
	await mockConversationStore(page, [
		{
			id: 'conv_export',
			title: 'Exportable question',
			created_at: TIMESTAMP,
			updated_at: TIMESTAMP,
			message_count: 2,
			messages: [
				{ id: 'u1', role: 'user', parts: [{ type: 'text', text: 'Exportable question' }] },
				{ id: 'a1', role: 'assistant', parts: [{ type: 'text', text: 'Exportable answer' }] }
			]
		}
	]);
	await page.goto('/overview');
	const dialog = await openAssistant(page);
	await dialog.getByRole('button', { name: 'Saved conversations' }).click();

	const download = page.waitForEvent('download');
	await dialog.getByRole('button', { name: 'Download conversation as Markdown' }).click();
	const file = await download;

	expect(file.suggestedFilename()).toBe('Exportable-question.md');
	const stream = await file.createReadStream();
	const chunks: Buffer[] = [];
	for await (const chunk of stream) chunks.push(chunk as Buffer);
	const markdown = Buffer.concat(chunks).toString('utf8');
	expect(markdown).toContain('# Exportable question');
	expect(markdown).toContain('Exportable answer');
});

test('attaches a PNG image to the prompt', async ({ page }) => {
	await mockConversationStore(page);
	let requestBody: Record<string, unknown> | undefined;
	await page.route('**/api/agent/chat', async (route) => {
		requestBody = route.request().postDataJSON();
		await route.fulfill(sse(textStream('msg_image', 'I can see it.')));
	});
	await page.goto('/overview');
	const dialog = await openAssistant(page);

	await dialog.locator('input[type="file"]').setInputFiles({
		name: 'screenshot.png',
		mimeType: 'image/png',
		buffer: Buffer.from(ONE_PIXEL_PNG, 'base64')
	});

	await expect(dialog.getByText('Please analyze this image.')).toBeVisible();
	await expect(dialog.getByText('I can see it.')).toBeVisible();
	const message = (requestBody?.messages as { parts: Record<string, unknown>[] }[])[0];
	expect(message.parts[0]).toEqual({ type: 'text', text: 'Please analyze this image.' });
	expect(message.parts[1]).toMatchObject({ type: 'file', mediaType: 'image/png' });
	expect(String(message.parts[1].url)).toMatch(/^data:image\/png;base64,/);
});

test('renders an assistant entity link with its entity component', async ({ page }) => {
	await mockConversationStore(page);
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill(
			sse([
				{ type: 'start', messageId: 'msg_entity_link' },
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
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
	const dialog = await openAssistant(page);
	await sendPrompt(dialog, 'Show my image build');

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
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
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
				{ type: 'message-metadata', messageMetadata: { createdAt: TIMESTAMP } },
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
		await route.fulfill(sse(textStream('msg_scroll', reply)));
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
