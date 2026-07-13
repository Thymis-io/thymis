import { expect, test } from '../playwright/fixtures';

test('opens and closes the floating Thymis Assistant', async ({ page }) => {
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
	await page.route('**/api/agent/chat', async (route) => {
		expect(route.request().postDataJSON()).toMatchObject({
			messages: [{ role: 'user', parts: [{ type: 'text', text: 'How is the fleet?' }] }]
		});
		await route.fulfill({
			contentType: 'text/event-stream',
			headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
			body:
				'data: {"type":"start","messageId":"msg_test"}\n\n' +
				'data: {"type":"start-step"}\n\n' +
				'data: {"type":"text-start","id":"text_1"}\n\n' +
				'data: {"type":"text-delta","id":"text_1","delta":"**Fleet** is healthy."}\n\n' +
				'data: {"type":"text-end","id":"text_1"}\n\n' +
				'data: {"type":"tool-input-available","toolCallId":"call_1","toolName":"get_state","input":{},"dynamic":true}\n\n' +
				'data: {"type":"tool-output-available","toolCallId":"call_1","output":{}}\n\n' +
				'data: {"type":"text-start","id":"text_2"}\n\n' +
				'data: {"type":"text-delta","id":"text_2","delta":" Current data loaded."}\n\n' +
				'data: {"type":"text-end","id":"text_2"}\n\n' +
				'data: {"type":"finish-step"}\n\n' +
				'data: {"type":"finish","finishReason":"stop"}\n\n' +
				'data: [DONE]\n\n'
		});
	});
	await page.goto('/overview');
	await page.waitForLoadState('networkidle');
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();

	const dialog = page.getByRole('dialog', { name: 'Thymis Assistant' });
	const input = dialog.getByRole('textbox', { name: 'Message Thymis Assistant' });
	await input.fill('How is the fleet?');
	await input.press('Enter');

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

test('renders an assistant entity link with its entity component', async ({ page }) => {
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill({
			contentType: 'text/event-stream',
			headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
			body:
				'data: {"type":"start","messageId":"msg_entity_link"}\n\n' +
				'data: {"type":"start-step"}\n\n' +
				'data: {"type":"text-start","id":"text_entity"}\n\n' +
				'data: {"type":"text-delta","id":"text_entity","delta":"The image build is ready:"}\n\n' +
				'data: {"type":"text-end","id":"text_entity"}\n\n' +
				'data: {"type":"data-entity-link","data":{"entityType":"task","identifier":"task-1","label":"build-device-image"}}\n\n' +
				'data: {"type":"finish-step"}\n\n' +
				'data: {"type":"finish","finishReason":"stop"}\n\n' +
				'data: [DONE]\n\n'
		});
	});
	await page.goto('/overview');
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).fill('Show my image build');
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).press('Enter');

	const link = page.getByRole('link', { name: 'build-device-image' });
	await expect(link).toHaveAttribute('href', '/tasks/task-1');
	await expect(link.locator('svg')).toBeVisible();
});

test('executes dashboard navigation emitted by the assistant', async ({ page }) => {
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill({
			contentType: 'text/event-stream',
			headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
			body:
				'data: {"type":"start","messageId":"msg_navigation"}\n\n' +
				'data: {"type":"start-step"}\n\n' +
				'data: {"type":"tool-input-available","toolCallId":"call_navigation","toolName":"navigate_frontend","input":{"destination":"tasks"},"dynamic":true}\n\n' +
				'data: {"type":"tool-output-available","toolCallId":"call_navigation","output":{"destination":"tasks","identifier":null}}\n\n' +
				'data: {"type":"finish-step"}\n\n' +
				'data: {"type":"finish","finishReason":"stop"}\n\n' +
				'data: [DONE]\n\n'
		});
	});
	await page.goto('/overview');
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();
	const input = page.getByRole('textbox', { name: 'Message Thymis Assistant' });
	await input.fill('Open my tasks');
	await input.press('Enter');

	await expect(page).toHaveURL(/\/tasks$/);
});

test('does not navigate to an unknown assistant-provided route', async ({ page }) => {
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill({
			contentType: 'text/event-stream',
			headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
			body:
				'data: {"type":"start","messageId":"msg_invalid_navigation"}\n\n' +
				'data: {"type":"start-step"}\n\n' +
				'data: {"type":"tool-input-available","toolCallId":"call_invalid_navigation","toolName":"navigate_frontend","input":{"destination":"not-a-route"},"dynamic":true}\n\n' +
				'data: {"type":"tool-output-available","toolCallId":"call_invalid_navigation","output":{}}\n\n' +
				'data: {"type":"finish-step"}\n\n' +
				'data: {"type":"finish","finishReason":"stop"}\n\n' +
				'data: [DONE]\n\n'
		});
	});
	await page.goto('/overview');
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();
	await page
		.getByRole('textbox', { name: 'Message Thymis Assistant' })
		.fill('Open an invalid route');
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).press('Enter');

	await expect(page).toHaveURL(/\/overview$/);
});

test('keeps a long streamed reply in view', async ({ page }) => {
	const reply = Array.from({ length: 80 }, (_, index) => `Result line ${index + 1}`).join('\n');
	await page.route('**/api/agent/chat', async (route) => {
		await route.fulfill({
			contentType: 'text/event-stream',
			headers: { 'x-vercel-ai-ui-message-stream': 'v1' },
			body:
				'data: {"type":"start","messageId":"msg_scroll"}\n\n' +
				'data: {"type":"start-step"}\n\n' +
				`data: ${JSON.stringify({ type: 'text-start', id: 'text_scroll' })}\n\n` +
				`data: ${JSON.stringify({ type: 'text-delta', id: 'text_scroll', delta: reply })}\n\n` +
				`data: ${JSON.stringify({ type: 'text-end', id: 'text_scroll' })}\n\n` +
				'data: {"type":"finish-step"}\n\n' +
				'data: {"type":"finish","finishReason":"stop"}\n\n' +
				'data: [DONE]\n\n'
		});
	});
	await page.goto('/overview');
	await page.getByRole('button', { name: 'Open Thymis Assistant' }).click();
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).fill('Show a long reply');
	await page.getByRole('textbox', { name: 'Message Thymis Assistant' }).press('Enter');
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
