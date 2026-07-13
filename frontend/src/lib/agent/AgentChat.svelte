<script lang="ts">
	import { Chat } from '@ai-sdk/svelte';
	import { DefaultChatTransport, type UIMessage } from 'ai';
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';
	import { goto } from '$app/navigation';
	import { frontendActionPath } from './navigation';
	import AssistantEntityLink from './AssistantEntityLink.svelte';
	import { isAssistantEntityLink, type AssistantEntityLink as EntityLink } from './entityLink';
	import { tick } from 'svelte';
	import { captureActiveVncScreenshot, vncScreenshotAvailable } from '$lib/vnc/screenshot';
	import type { GlobalState } from '$lib/state.svelte';
	import Bot from 'lucide-svelte/icons/bot';
	import Camera from 'lucide-svelte/icons/camera';
	import LoaderCircle from 'lucide-svelte/icons/loader-circle';
	import MessageCircle from 'lucide-svelte/icons/message-circle';
	import Send from 'lucide-svelte/icons/send';
	import Square from 'lucide-svelte/icons/square';
	import Trash2 from 'lucide-svelte/icons/trash-2';
	import X from 'lucide-svelte/icons/x';

	interface Props {
		globalState: GlobalState;
	}

	let { globalState }: Props = $props();
	const renderMarkdown = (markdown: string) =>
		DOMPurify.sanitize(marked.parse(markdown, { async: false }));

	type ToolPart = {
		type: string;
		state: string;
		toolCallId?: string;
		toolName?: string;
		input?: unknown;
	};

	const isToolPart = (
		part: UIMessage['parts'][number]
	): part is UIMessage['parts'][number] & ToolPart =>
		part.type === 'dynamic-tool' || part.type.startsWith('tool-');

	const isEntityLinkPart = (
		part: UIMessage['parts'][number]
	): part is UIMessage['parts'][number] & { type: 'data-entity-link'; data: EntityLink } =>
		part.type === 'data-entity-link' && isAssistantEntityLink(part.data);

	const isVisibleToolPart = (part: UIMessage['parts'][number]) =>
		isToolPart(part) && part.toolName !== 'link_entity';

	const toolName = (part: ToolPart) =>
		(part.toolName ?? part.type.replace(/^tool-/, '')).replaceAll('_', ' ');

	const frontendActionCalls = new Set<string>();

	let open = $state(false);
	let shouldFollowLatest = $state(true);
	let input = $state('');
	let messageList = $state<HTMLDivElement>();
	const chat = new Chat({ transport: new DefaultChatTransport({ api: '/api/agent/chat' }) });
	let messages = $derived(chat.messages);
	let streaming = $derived(chat.status === 'submitted' || chat.status === 'streaming');
	let errorMessage = $derived(chat.error?.message);
	let attachmentError = $state<string>();

	$effect(() => {
		for (const message of messages) {
			for (const part of message.parts) {
				if (!isToolPart(part) || part.state !== 'output-available' || !part.toolCallId) continue;
				const name = part.toolName ?? part.type.replace(/^tool-/, '');
				if (frontendActionCalls.has(part.toolCallId)) continue;
				if (name === 'navigate_frontend') {
					const path = frontendActionPath(part.input);
					if (path) {
						frontendActionCalls.add(part.toolCallId);
						void goto(path);
					}
				}
			}
		}
	});

	const scrollToLatestMessage = async () => {
		await tick();
		messageList?.scrollTo({ top: messageList.scrollHeight });
	};

	const updateMessageScrollPosition = () => {
		if (!messageList) return;
		shouldFollowLatest =
			messageList.scrollHeight - messageList.scrollTop - messageList.clientHeight < 24;
	};

	$effect(() => {
		if (open && shouldFollowLatest) {
			messages;
			streaming;
			void scrollToLatestMessage();
		}
	});

	const clearConversation = () => {
		chat.messages = [];
		chat.clearError();
	};

	const stop = () => void chat.stop();

	const send = async () => {
		const content = input.trim();
		if (!content || streaming) return;

		shouldFollowLatest = true;
		attachmentError = undefined;
		input = '';
		await chat.sendMessage({ text: content });
		await scrollToLatestMessage();
	};

	const attachVncScreenshot = async () => {
		if (streaming || !$vncScreenshotAvailable) return;

		attachmentError = undefined;
		try {
			const screenshot = await captureActiveVncScreenshot();
			const url = await new Promise<string>((resolve, reject) => {
				const reader = new FileReader();
				reader.onerror = () => reject(new Error('Could not read the VNC screenshot.'));
				reader.onload = () => resolve(String(reader.result));
				reader.readAsDataURL(screenshot);
			});

			shouldFollowLatest = true;
			await chat.sendMessage({
				parts: [
					{ type: 'text', text: 'Please analyze this screenshot from the current VNC session.' },
					{
						type: 'file',
						mediaType: screenshot.type,
						filename: screenshot.name,
						url
					}
				]
			});
			await scrollToLatestMessage();
		} catch (error) {
			attachmentError =
				error instanceof Error ? error.message : 'Could not attach the VNC screenshot.';
		}
	};

	const handleInputKeydown = (event: KeyboardEvent) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			void send();
		}
	};
</script>

<div class="assistant-root">
	{#if open}
		<dialog
			id="thymis-assistant"
			class="assistant-window"
			aria-label="Thymis Assistant"
			aria-modal="false"
			open
		>
			<header class="assistant-header">
				<div class="assistant-title">
					<span class="assistant-mark"><Bot size={18} /></span>
					<span>
						<strong>Thymis Assistant</strong>
						<small>Can inspect, change, and act on controller data</small>
					</span>
				</div>
				<div class="assistant-actions">
					{#if messages.length > 0}
						<button
							class="assistant-icon-button"
							type="button"
							onclick={clearConversation}
							aria-label="Clear conversation"
							title="Clear conversation"
						>
							<Trash2 size={16} />
						</button>
					{/if}
					<button
						class="assistant-icon-button"
						type="button"
						onclick={() => (open = false)}
						aria-label="Close Thymis Assistant"
						title="Close"
					>
						<X size={18} />
					</button>
				</div>
			</header>

			<div
				class="assistant-messages"
				bind:this={messageList}
				onscroll={updateMessageScrollPosition}
				aria-live="polite"
			>
				{#if messages.length === 0}
					<div class="assistant-empty">
						<Bot size={24} class="assistant-empty-icon" />
						<p>Ask about devices, fleet health, configurations, tasks, or repository state.</p>
						<span
							>The assistant can inspect controller data, apply requested changes, and open relevant
							dashboard pages.</span
						>
					</div>
				{:else}
					{#each messages as message, index (message.id)}
						{@const hasVisibleParts = message.parts.some(
							(part) =>
								(part.type === 'text' && part.text) ||
								isEntityLinkPart(part) ||
								isVisibleToolPart(part)
						)}
						{#if hasVisibleParts || (streaming && index === messages.length - 1)}
							<div
								class:assistant-message={message.role === 'assistant'}
								class:user-message={message.role === 'user'}
							>
								{#if message.role === 'assistant'}
									<Bot size={16} class="assistant-message-icon" />
								{/if}
								<div class="assistant-message-content">
									{#each message.parts as part}
										{#if part.type === 'text' && part.text}
											<div class="assistant-markdown">{@html renderMarkdown(part.text)}</div>
										{:else if isEntityLinkPart(part)}
											<AssistantEntityLink {globalState} entity={part.data} />
										{:else if isVisibleToolPart(part)}
											<div
												class:assistant-tool-complete={part.state === 'output-available'}
												class="assistant-tool"
											>
												{#if part.state === 'output-available'}
													<Bot size={14} />
												{:else}
													<LoaderCircle size={14} class="animate-spin" />
												{/if}
												<span>{toolName(part)}</span>
											</div>
										{/if}
									{/each}
								</div>
							</div>
						{/if}
					{/each}
				{/if}
			</div>

			{#if streaming}
				<div class="assistant-status" aria-live="polite">
					<LoaderCircle size={15} class="animate-spin" />
					Thinking…
					<button type="button" onclick={stop}><Square size={12} /> Stop</button>
				</div>
			{/if}
			{#if errorMessage || attachmentError}
				<p class="assistant-error" role="alert">{attachmentError ?? errorMessage}</p>
			{/if}

			<form
				class="assistant-composer"
				onsubmit={(event) => {
					event.preventDefault();
					void send();
				}}
			>
				<button
					class="assistant-attachment-button"
					type="button"
					onclick={() => void attachVncScreenshot()}
					disabled={!$vncScreenshotAvailable || streaming}
					aria-label="Attach current VNC screenshot"
					title="Attach current VNC screenshot"
				>
					<Camera size={17} />
				</button>
				<textarea
					bind:value={input}
					onkeydown={handleInputKeydown}
					placeholder="Ask Thymis…"
					aria-label="Message Thymis Assistant"
					rows="2"
					disabled={streaming}></textarea>
				<button type="submit" aria-label="Send message" disabled={!input.trim() || streaming}>
					<Send size={17} />
				</button>
			</form>
		</dialog>
	{/if}

	<button
		class="assistant-launcher"
		type="button"
		onclick={() => (open = !open)}
		aria-label={open ? 'Close Thymis Assistant' : 'Open Thymis Assistant'}
		aria-expanded={open}
		aria-controls="thymis-assistant"
		title="Thymis Assistant"
	>
		{#if open}
			<X size={23} />
		{:else}
			<MessageCircle size={23} />
		{/if}
	</button>
</div>

<style lang="postcss">
	.assistant-root {
		position: fixed;
		right: 18px;
		bottom: 54px;
		z-index: 70;
	}
	.assistant-launcher {
		width: 48px;
		height: 48px;
		border: 0;
		border-radius: 50%;
		display: grid;
		place-items: center;
		color: white;
		background: var(--ds-accent);
		box-shadow: var(--ds-shadow-lg);
		transition:
			background 0.12s,
			transform 0.12s;
	}
	.assistant-launcher:hover {
		background: var(--ds-accent-strong);
		transform: translateY(-1px);
	}
	.assistant-window {
		position: absolute;
		inset: auto 0 60px auto;
		width: min(390px, calc(100vw - 24px));
		height: min(590px, calc(100vh - 82px));
		margin: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		border: 1px solid var(--ds-border);
		border-radius: var(--ds-radius-lg);
		background: var(--ds-surface);
		box-shadow: var(--ds-shadow-lg);
	}
	.assistant-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border-bottom: 1px solid var(--ds-border);
	}
	.assistant-title,
	.assistant-actions,
	.assistant-status,
	.assistant-composer {
		display: flex;
		align-items: center;
	}
	.assistant-title {
		gap: 9px;
		min-width: 0;
	}
	.assistant-title strong,
	.assistant-title small {
		display: block;
	}
	.assistant-title strong {
		font-size: 13px;
		font-weight: 650;
		color: var(--ds-text);
	}
	.assistant-title small {
		margin-top: 1px;
		font-size: 11px;
		color: var(--ds-text-mute);
	}
	.assistant-mark {
		width: 30px;
		height: 30px;
		display: grid;
		place-items: center;
		border-radius: 8px;
		color: var(--ds-accent);
		background: var(--ds-accent-dim);
	}
	.assistant-actions {
		gap: 2px;
	}
	.assistant-icon-button {
		width: 30px;
		height: 30px;
		display: grid;
		place-items: center;
		border-radius: 6px;
		color: var(--ds-text-dim);
	}
	.assistant-icon-button:hover {
		color: var(--ds-text);
		background: var(--ds-surface-3);
	}
	.assistant-messages {
		flex: 1;
		overflow-y: auto;
		padding: 14px;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.assistant-empty {
		max-width: 270px;
		margin: auto;
		text-align: center;
		color: var(--ds-text-dim);
	}
	:global(.assistant-empty-icon) {
		margin: 0 auto 10px;
		color: var(--ds-accent);
	}
	.assistant-empty p {
		margin: 0;
		font-size: 13px;
		font-weight: 500;
		color: var(--ds-text);
	}
	.assistant-empty span {
		display: block;
		margin-top: 6px;
		font-size: 12px;
		line-height: 1.45;
	}
	.assistant-message,
	.user-message {
		display: flex;
		gap: 7px;
		max-width: 88%;
		padding: 9px 11px;
		border-radius: 10px;
		font-size: 13px;
		line-height: 1.45;
		word-break: break-word;
	}
	.assistant-message {
		align-self: flex-start;
		color: var(--ds-text);
		background: var(--ds-surface-3);
	}
	.user-message {
		align-self: flex-end;
		color: white;
		background: var(--ds-accent);
	}
	:global(.assistant-message-icon) {
		flex: none;
		margin-top: 1px;
		color: var(--ds-accent);
	}
	.assistant-message-content {
		min-width: 0;
	}
	.assistant-markdown :global(p:first-child),
	.assistant-markdown :global(h1:first-child),
	.assistant-markdown :global(h2:first-child),
	.assistant-markdown :global(h3:first-child) {
		margin-top: 0;
	}
	.assistant-markdown :global(p:last-child),
	.assistant-markdown :global(ul:last-child),
	.assistant-markdown :global(ol:last-child),
	.assistant-markdown :global(pre:last-child) {
		margin-bottom: 0;
	}
	.assistant-markdown :global(p),
	.assistant-markdown :global(ul),
	.assistant-markdown :global(ol) {
		margin: 0 0 8px;
	}
	.assistant-markdown :global(ul),
	.assistant-markdown :global(ol) {
		padding-left: 18px;
	}
	.assistant-markdown :global(code) {
		padding: 1px 4px;
		border-radius: 4px;
		background: color-mix(in srgb, var(--ds-text) 10%, transparent);
		font-family: var(--font-mono);
		font-size: 0.92em;
	}
	.assistant-markdown :global(pre) {
		overflow-x: auto;
		padding: 8px;
		border-radius: 6px;
		background: var(--ds-surface);
	}
	.assistant-markdown :global(pre code) {
		padding: 0;
		background: none;
	}
	.assistant-markdown :global(a) {
		color: var(--ds-accent);
		text-decoration: underline;
	}
	.assistant-tool {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-top: 8px;
		font-size: 11.5px;
		color: var(--ds-text-dim);
	}
	.assistant-tool-complete {
		color: var(--ds-success);
	}
	.assistant-status {
		gap: 6px;
		padding: 8px 14px;
		border-top: 1px solid var(--ds-border);
		font-size: 11.5px;
		color: var(--ds-text-dim);
	}
	.assistant-status button {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		margin-left: auto;
		font-size: 11px;
		color: var(--ds-text-dim);
	}
	.assistant-status button:hover {
		color: var(--ds-text);
	}
	.assistant-error {
		margin: 0;
		padding: 8px 14px;
		border-top: 1px solid var(--ds-danger);
		background: var(--ds-danger-dim);
		font-size: 12px;
		color: var(--ds-danger);
	}
	.assistant-composer {
		align-items: flex-end;
		gap: 8px;
		padding: 11px;
		border-top: 1px solid var(--ds-border);
		background: var(--ds-surface-2);
	}
	.assistant-composer textarea {
		min-height: 40px;
		max-height: 92px;
		resize: none;
		flex: 1;
		border: 1px solid var(--ds-border-strong);
		border-radius: 8px;
		background: var(--ds-surface);
		color: var(--ds-text);
		font-size: 13px;
		line-height: 1.35;
	}
	.assistant-composer textarea:focus {
		border-color: var(--ds-accent);
		box-shadow: 0 0 0 2px var(--ds-accent-dim);
	}
	.assistant-composer button {
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		flex: none;
		border-radius: 8px;
		color: white;
		background: var(--ds-accent);
	}
	.assistant-composer .assistant-attachment-button {
		color: var(--ds-text-dim);
		background: var(--ds-surface);
		border: 1px solid var(--ds-border-strong);
	}
	.assistant-composer .assistant-attachment-button:not(:disabled):hover {
		color: var(--ds-text);
		background: var(--ds-surface-3);
	}
	.assistant-composer button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}
	@media (max-width: 640px) {
		.assistant-root {
			right: 12px;
			bottom: 50px;
		}
		.assistant-window {
			height: min(570px, calc(100vh - 74px));
		}
	}
</style>
