<script lang="ts">
	import { Chat } from '@ai-sdk/svelte';
	import { DefaultChatTransport, type UIMessage } from 'ai';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { tick } from 'svelte';
	import { _ } from 'svelte-i18n';
	import AssistantEntityLink from './AssistantEntityLink.svelte';
	import AssistantMarkdown from './AssistantMarkdown.svelte';
	import { isAssistantEntityLink, type AssistantEntityLink as EntityLink } from './entityLink';
	import { frontendActionPath } from './navigation';
	import {
		createConversation,
		deleteConversation,
		downloadMarkdown,
		getConversation,
		listConversations,
		renameConversation,
		transcriptMarkdown,
		type AssistantConversationSummary
	} from './conversations';
	import { captureActiveVncScreenshot, vncScreenshotAvailable } from '$lib/vnc/screenshot';
	import type { GlobalState } from '$lib/state.svelte';
	import Bot from 'lucide-svelte/icons/bot';
	import Camera from 'lucide-svelte/icons/camera';
	import Check from 'lucide-svelte/icons/check';
	import Copy from 'lucide-svelte/icons/copy';
	import Download from 'lucide-svelte/icons/download';
	import History from 'lucide-svelte/icons/history';
	import ImagePlus from 'lucide-svelte/icons/image-plus';
	import LoaderCircle from 'lucide-svelte/icons/loader-circle';
	import MessageCircle from 'lucide-svelte/icons/message-circle';
	import Pencil from 'lucide-svelte/icons/pencil';
	import Plus from 'lucide-svelte/icons/plus';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import Search from 'lucide-svelte/icons/search';
	import Send from 'lucide-svelte/icons/send';
	import Square from 'lucide-svelte/icons/square';
	import Trash2 from 'lucide-svelte/icons/trash-2';
	import X from 'lucide-svelte/icons/x';

	interface Props {
		globalState: GlobalState;
	}

	let { globalState }: Props = $props();

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

	const isVisibleToolPart = (
		part: UIMessage['parts'][number]
	): part is UIMessage['parts'][number] & ToolPart =>
		isToolPart(part) && part.toolName !== 'link_entity';

	const isImageAttachmentPart = (
		part: UIMessage['parts'][number]
	): part is UIMessage['parts'][number] & { type: 'file'; mediaType: string; url: string } =>
		part.type === 'file' && part.mediaType.startsWith('image/') && Boolean(part.url);

	const toolName = (part: ToolPart) =>
		(part.toolName ?? part.type.replace(/^tool-/, '')).replaceAll('_', ' ');

	const messageText = (message: UIMessage) =>
		message.parts
			.filter((part) => part.type === 'text')
			.map((part) => part.text)
			.join('\n\n')
			.trim();

	const messageCreatedAt = (message: UIMessage) => {
		const metadata = message.metadata as { createdAt?: unknown } | undefined;
		const createdAt = typeof metadata?.createdAt === 'string' ? metadata.createdAt : undefined;
		return createdAt ? new Date(createdAt) : undefined;
	};

	const readAsDataUrl = (file: File) =>
		new Promise<string>((resolve, reject) => {
			const reader = new FileReader();
			reader.onerror = () => reject(new Error('Could not read the file.'));
			reader.onload = () => resolve(String(reader.result));
			reader.readAsDataURL(file);
		});

	const frontendActionCalls = new Set<string>();

	// Other tabs of the same operator share one conversation store.
	const channel = browser ? new BroadcastChannel('thymis-assistant') : undefined;
	const broadcast = () => channel?.postMessage({ type: 'refresh' });

	let open = $state(false);
	let shouldFollowLatest = $state(true);
	let input = $state('');
	let messageList = $state<HTMLDivElement>();
	let inputField = $state<HTMLTextAreaElement>();
	let launcher = $state<HTMLButtonElement>();
	let attachInput = $state<HTMLInputElement>();
	let conversations = $state<AssistantConversationSummary[]>([]);
	let activeConversationId = $state<string | null>(null);
	let historyOpen = $state(false);
	let loadingConversation = $state(false);
	let conversationError = $state<string>();
	let conversationQuery = $state('');
	let renamingId = $state<string | null>(null);
	let renameValue = $state('');
	let copiedMessageId = $state<string | null>(null);
	let started = false;

	const transport = new DefaultChatTransport({
		api: '/api/agent/chat',
		// The controller keeps the transcript; only the newest message is sent, so
		// a long conversation never re-uploads its whole history.
		prepareSendMessagesRequest: ({ messages: outgoing, body, trigger, messageId }) => ({
			body: {
				...body,
				conversation_id: activeConversationId,
				trigger,
				messageId,
				messages: outgoing.slice(-1)
			}
		})
	});
	const chat = new Chat({
		transport,
		onFinish: () => {
			void refreshConversations();
			broadcast();
		}
	});
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

	$effect(() => {
		if (!open || started) return;
		started = true;
		void loadSavedConversations();
	});

	$effect(() => {
		if (!open) return;
		void tick().then(() => inputField?.focus());
	});

	$effect(() => {
		if (!channel) return;
		const onMessage = () => {
			void refreshConversations();
			if (activeConversationId && !streaming) {
				void loadConversation(activeConversationId);
			}
		};
		channel.addEventListener('message', onMessage);
		return () => channel.removeEventListener('message', onMessage);
	});

	const refreshConversations = async (query: string = conversationQuery) => {
		const requested = query;
		const listed = await listConversations(requested);
		// A newer keystroke may have overtaken this response.
		if (requested !== conversationQuery) return;
		conversations = listed;
	};

	/**
	 * A saved transcript replays its tool calls, but a restored
	 * `navigate_frontend` call already ran when it was first streamed and must not
	 * move the operator again.
	 */
	const markLoadedFrontendActions = (loaded: UIMessage[]) => {
		for (const message of loaded) {
			for (const part of message.parts) {
				if (!isToolPart(part) || !part.toolCallId) continue;
				if ((part.toolName ?? part.type.replace(/^tool-/, '')) === 'navigate_frontend') {
					frontendActionCalls.add(part.toolCallId);
				}
			}
		}
	};

	const loadConversation = async (id: string) => {
		loadingConversation = true;
		conversationError = undefined;
		const conversation = await getConversation(id);
		loadingConversation = false;
		if (!conversation) {
			resetConversation();
			await refreshConversations();
			return;
		}
		activeConversationId = conversation.id;
		markLoadedFrontendActions(conversation.messages);
		chat.messages = conversation.messages;
		chat.clearError();
		attachmentError = undefined;
		shouldFollowLatest = true;
		await scrollToLatestMessage();
	};

	const selectConversation = async (id: string) => {
		if (streaming) return;
		historyOpen = false;
		if (id === activeConversationId) return;
		await loadConversation(id);
	};

	const loadSavedConversations = async () => {
		loadingConversation = true;
		conversationError = undefined;
		try {
			await refreshConversations();
			const mostRecent = conversations[0];
			if (mostRecent) {
				loadingConversation = false;
				await loadConversation(mostRecent.id);
			}
		} catch (error) {
			conversationError = error instanceof Error ? error.message : $_('assistant.error-load');
		} finally {
			loadingConversation = false;
		}
	};

	const resetConversation = () => {
		activeConversationId = null;
		chat.messages = [];
		chat.clearError();
		attachmentError = undefined;
		conversationError = undefined;
	};

	const startNewChat = () => {
		if (streaming) return;
		historyOpen = false;
		resetConversation();
	};

	const removeConversation = async (id: string) => {
		if (streaming || !(await deleteConversation(id))) return;
		if (id === activeConversationId) resetConversation();
		await refreshConversations();
		broadcast();
	};

	const ensureConversation = async (): Promise<boolean> => {
		if (activeConversationId) return true;
		const conversation = await createConversation();
		if (!conversation) {
			conversationError = $_('assistant.error-new');
			return false;
		}
		activeConversationId = conversation.id;
		conversations = [conversation, ...conversations];
		broadcast();
		return true;
	};

	const startRename = (conversation: AssistantConversationSummary) => {
		renamingId = conversation.id;
		renameValue = conversation.title;
	};

	const submitRename = async () => {
		const id = renamingId;
		const title = renameValue.trim();
		renamingId = null;
		if (!id || !title) return;
		if (!(await renameConversation(id, title))) {
			conversationError = $_('assistant.error-rename');
			return;
		}
		await refreshConversations();
		broadcast();
	};

	const exportActiveConversation = () => {
		const title =
			conversations.find((conversation) => conversation.id === activeConversationId)?.title ??
			$_('assistant.title');
		downloadMarkdown(title, transcriptMarkdown(title, messages));
	};

	const copyMessage = async (message: UIMessage) => {
		await navigator.clipboard.writeText(messageText(message));
		copiedMessageId = message.id;
		setTimeout(() => {
			if (copiedMessageId === message.id) copiedMessageId = null;
		}, 2000);
	};

	const regenerate = async (messageId?: string) => {
		if (streaming) return;
		chat.clearError();
		attachmentError = undefined;
		shouldFollowLatest = true;
		await chat.regenerate(messageId === undefined ? undefined : { messageId });
		await scrollToLatestMessage();
	};

	const stop = () => void chat.stop();

	const send = async (text: string, dataUrl?: string) => {
		if (streaming || !(await ensureConversation())) return;
		shouldFollowLatest = true;
		await chat.sendMessage({
			metadata: { createdAt: new Date().toISOString() },
			parts:
				dataUrl === undefined
					? [{ type: 'text' as const, text }]
					: [
							{ type: 'text' as const, text },
							{
								type: 'file' as const,
								mediaType: 'image/png',
								filename: 'vnc-screenshot.png',
								url: dataUrl
							}
						]
		});
		await scrollToLatestMessage();
	};

	const sendTypedMessage = async () => {
		const content = input.trim();
		if (!content || streaming) return;
		attachmentError = undefined;
		input = '';
		await send(content);
	};

	const attachVncScreenshot = async () => {
		if (streaming || !$vncScreenshotAvailable) return;
		attachmentError = undefined;
		try {
			const screenshot = await captureActiveVncScreenshot();
			await send($_('assistant.screenshot-prompt'), await readAsDataUrl(screenshot));
		} catch (error) {
			attachmentError = error instanceof Error ? error.message : $_('assistant.error-screenshot');
		}
	};

	const attachImage = async (event: Event) => {
		const field = event.currentTarget as HTMLInputElement;
		const file = field.files?.[0];
		field.value = '';
		if (!file || streaming) return;
		attachmentError = undefined;
		if (file.type !== 'image/png') {
			attachmentError = $_('assistant.error-image-type');
			return;
		}
		try {
			await send($_('assistant.image-prompt'), await readAsDataUrl(file));
		} catch (error) {
			attachmentError = error instanceof Error ? error.message : $_('assistant.error-image');
		}
	};

	const closeAssistant = () => {
		open = false;
		void tick().then(() => launcher?.focus());
	};

	const handleDialogKeydown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			event.stopPropagation();
			closeAssistant();
		}
	};

	const handleInputKeydown = (event: KeyboardEvent) => {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			void sendTypedMessage();
		}
	};
</script>

<div class="assistant-root">
	{#if open}
		<dialog
			id="thymis-assistant"
			class="assistant-window"
			aria-label={$_('assistant.title')}
			aria-modal="false"
			open
			onkeydown={handleDialogKeydown}
		>
			<header class="assistant-header">
				<div class="assistant-title">
					<span class="assistant-mark"><Bot size={18} /></span>
					<span>
						<strong>{$_('assistant.title')}</strong>
						<small>{$_('assistant.subtitle')}</small>
					</span>
				</div>
				<div class="assistant-actions">
					<button
						class="assistant-icon-button"
						type="button"
						onclick={startNewChat}
						disabled={streaming}
						aria-label={$_('assistant.new-conversation')}
						title={$_('assistant.new-conversation')}
					>
						<Plus size={16} />
					</button>
					<button
						class="assistant-icon-button"
						class:assistant-icon-active={historyOpen}
						type="button"
						onclick={() => (historyOpen = !historyOpen)}
						aria-label={$_('assistant.saved-conversations')}
						aria-pressed={historyOpen}
						title={$_('assistant.saved-conversations')}
					>
						<History size={16} />
					</button>
					<button
						class="assistant-icon-button"
						type="button"
						onclick={closeAssistant}
						aria-label={$_('assistant.close')}
						title={$_('common.cancel')}
					>
						<X size={18} />
					</button>
				</div>
			</header>

			{#if historyOpen}
				<div class="assistant-history" aria-label={$_('assistant.saved-conversations')}>
					<div class="assistant-history-toolbar">
						<label class="assistant-search">
							<Search size={14} />
							<input
								type="search"
								bind:value={conversationQuery}
								oninput={() => void refreshConversations()}
								placeholder={$_('assistant.search-placeholder')}
								aria-label={$_('assistant.search-placeholder')}
							/>
						</label>
						<button
							class="assistant-icon-button"
							type="button"
							onclick={exportActiveConversation}
							disabled={messages.length === 0}
							aria-label={$_('assistant.export-conversation')}
							title={$_('assistant.export-conversation')}
						>
							<Download size={15} />
						</button>
					</div>
					{#if conversations.length === 0}
						<p class="assistant-history-empty">
							{conversationQuery
								? $_('assistant.search-empty')
								: $_('assistant.saved-conversations-empty')}
						</p>
					{:else}
						<ul>
							{#each conversations as conversation (conversation.id)}
								<li>
									{#if renamingId === conversation.id}
										<form
											class="assistant-rename"
											onsubmit={(event) => {
												event.preventDefault();
												void submitRename();
											}}
										>
											<input
												bind:value={renameValue}
												maxlength="120"
												aria-label={$_('assistant.rename-conversation')}
											/>
											<button
												class="assistant-icon-button"
												type="submit"
												aria-label={$_('common.save')}
												title={$_('common.save')}
											>
												<Check size={15} />
											</button>
											<button
												class="assistant-icon-button"
												type="button"
												onclick={() => (renamingId = null)}
												aria-label={$_('common.cancel')}
												title={$_('common.cancel')}
											>
												<X size={15} />
											</button>
										</form>
									{:else}
										<button
											class="assistant-history-item"
											class:assistant-history-item-active={conversation.id === activeConversationId}
											type="button"
											onclick={() => void selectConversation(conversation.id)}
										>
											<span>{conversation.title}</span>
											<small>
												{$_(
													conversation.message_count === 1
														? 'assistant.message-count'
														: 'assistant.message-count-plural',
													{ values: { count: conversation.message_count } }
												)}
											</small>
										</button>
										<button
											class="assistant-icon-button"
											type="button"
											onclick={() => startRename(conversation)}
											aria-label={$_('assistant.rename-conversation')}
											title={$_('assistant.rename-conversation')}
										>
											<Pencil size={15} />
										</button>
										<button
											class="assistant-icon-button"
											type="button"
											onclick={() => void removeConversation(conversation.id)}
											aria-label={$_('assistant.delete-conversation-named', {
												values: { title: conversation.title }
											})}
											title={$_('assistant.delete-conversation')}
										>
											<Trash2 size={15} />
										</button>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			{:else}
				<div
					class="assistant-messages"
					bind:this={messageList}
					onscroll={updateMessageScrollPosition}
					aria-live="polite"
				>
					{#if loadingConversation}
						<div class="assistant-empty">
							<LoaderCircle size={24} class="assistant-empty-icon animate-spin" />
							<p>{$_('assistant.loading-conversation')}</p>
						</div>
					{:else if messages.length === 0}
						<div class="assistant-empty">
							<Bot size={24} class="assistant-empty-icon" />
							<p>{$_('assistant.empty-title')}</p>
							<span>{$_('assistant.empty-hint')}</span>
						</div>
					{:else}
						{#each messages as message, index (message.id)}
							{@const createdAt = messageCreatedAt(message)}
							{@const text = messageText(message)}
							{@const hasVisibleParts = message.parts.some(
								(part) =>
									(part.type === 'text' && part.text) ||
									isEntityLinkPart(part) ||
									isImageAttachmentPart(part) ||
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
												<div class="assistant-markdown">
													<AssistantMarkdown
														markdown={part.text}
														complete={part.state !== 'streaming'}
													/>
												</div>
											{:else if isEntityLinkPart(part)}
												<AssistantEntityLink {globalState} entity={part.data} />
											{:else if isImageAttachmentPart(part)}
												<img
													class="assistant-attachment"
													src={part.url}
													alt={part.filename ?? $_('assistant.attach-image')}
												/>
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
										<div class="assistant-message-footer">
											{#if createdAt}
												<time class="assistant-time" datetime={createdAt.toISOString()}>
													{createdAt.toLocaleString(undefined, {
														dateStyle: 'short',
														timeStyle: 'short'
													})}
												</time>
											{/if}
											{#if text}
												<button
													class="assistant-message-action"
													type="button"
													onclick={() => void copyMessage(message)}
													aria-label={$_('assistant.copy-response')}
													title={$_('assistant.copy-response')}
												>
													{#if copiedMessageId === message.id}
														<Check size={12} />
													{:else}
														<Copy size={12} />
													{/if}
												</button>
											{/if}
											{#if message.role === 'assistant' && index === messages.length - 1}
												<button
													class="assistant-message-action"
													type="button"
													onclick={() => void regenerate(message.id)}
													disabled={streaming}
													aria-label={$_('assistant.regenerate')}
													title={$_('assistant.regenerate')}
												>
													<RotateCcw size={12} />
												</button>
											{/if}
										</div>
									</div>
								</div>
							{/if}
						{/each}
					{/if}
				</div>
			{/if}

			{#if streaming}
				<div class="assistant-status" aria-live="polite">
					<LoaderCircle size={15} class="animate-spin" />
					{$_('assistant.thinking')}
					<button type="button" onclick={stop}>
						<Square size={12} />
						{$_('assistant.stop')}
					</button>
				</div>
			{/if}
			{#if errorMessage || attachmentError || conversationError}
				<p class="assistant-error" role="alert">
					{attachmentError ?? conversationError ?? errorMessage}
					{#if errorMessage}
						<button type="button" onclick={() => void regenerate()}>
							<RotateCcw size={12} />
							{$_('assistant.retry')}
						</button>
					{/if}
				</p>
			{/if}

			<form
				class="assistant-composer"
				onsubmit={(event) => {
					event.preventDefault();
					void sendTypedMessage();
				}}
			>
				<input
					class="assistant-file-input"
					bind:this={attachInput}
					type="file"
					accept="image/png"
					onchange={(event) => void attachImage(event)}
					tabindex="-1"
					aria-hidden="true"
				/>
				<button
					class="assistant-attachment-button"
					type="button"
					onclick={() => attachInput?.click()}
					disabled={streaming}
					aria-label={$_('assistant.attach-image')}
					title={$_('assistant.attach-image')}
				>
					<ImagePlus size={17} />
				</button>
				<button
					class="assistant-attachment-button"
					type="button"
					onclick={() => void attachVncScreenshot()}
					disabled={!$vncScreenshotAvailable || streaming}
					aria-label={$_('assistant.attach-screenshot')}
					title={$_('assistant.attach-screenshot')}
				>
					<Camera size={17} />
				</button>
				<textarea
					bind:this={inputField}
					bind:value={input}
					onkeydown={handleInputKeydown}
					placeholder={$_('assistant.input-placeholder')}
					aria-label={$_('assistant.input-label')}
					rows="2"
					disabled={streaming}></textarea>
				<button
					type="submit"
					aria-label={$_('assistant.send')}
					disabled={!input.trim() || streaming}
				>
					<Send size={17} />
				</button>
			</form>
		</dialog>
	{/if}

	<button
		class="assistant-launcher"
		type="button"
		bind:this={launcher}
		onclick={() => (open ? closeAssistant() : (open = true))}
		aria-label={open ? $_('assistant.close') : $_('assistant.open')}
		aria-expanded={open}
		aria-controls="thymis-assistant"
		title={$_('assistant.title')}
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
	.assistant-icon-button:disabled {
		cursor: not-allowed;
		opacity: 0.45;
	}
	.assistant-icon-active {
		color: var(--ds-accent);
		background: var(--ds-accent-dim);
	}
	.assistant-history {
		flex: 1;
		overflow-y: auto;
		padding: 8px;
	}
	.assistant-history-toolbar {
		display: flex;
		align-items: center;
		gap: 4px;
		margin-bottom: 6px;
	}
	.assistant-search {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 0 8px;
		border: 1px solid var(--ds-border-strong);
		border-radius: 8px;
		color: var(--ds-text-mute);
		background: var(--ds-surface);
	}
	.assistant-search input {
		flex: 1;
		min-width: 0;
		border: 0;
		background: none;
		font-size: 12.5px;
		color: var(--ds-text);
	}
	.assistant-search input:focus {
		outline: none;
	}
	.assistant-rename {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.assistant-rename input {
		flex: 1;
		min-width: 0;
		padding: 6px 8px;
		border: 1px solid var(--ds-accent);
		border-radius: 8px;
		background: var(--ds-surface);
		font-size: 13px;
		color: var(--ds-text);
	}
	.assistant-history ul {
		margin: 0;
		padding: 0;
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.assistant-history li {
		display: flex;
		align-items: center;
		gap: 2px;
	}
	.assistant-history-item {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 2px;
		padding: 8px 10px;
		border-radius: 8px;
		text-align: left;
	}
	.assistant-history-item:hover {
		background: var(--ds-surface-3);
	}
	.assistant-history-item-active {
		background: var(--ds-accent-dim);
	}
	.assistant-history-item span {
		width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 13px;
		color: var(--ds-text);
	}
	.assistant-history-item-active span {
		color: var(--ds-accent);
		font-weight: 600;
	}
	.assistant-history-item small {
		font-size: 11px;
		color: var(--ds-text-mute);
	}
	.assistant-history-empty {
		margin: 24px 12px;
		text-align: center;
		font-size: 12.5px;
		color: var(--ds-text-dim);
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
	.assistant-message-footer {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-top: 5px;
		opacity: 0.7;
	}
	.assistant-time {
		font-size: 10.5px;
		color: var(--ds-text-mute);
	}
	.user-message .assistant-time {
		color: color-mix(in srgb, white 78%, transparent);
	}
	.assistant-message-action {
		display: inline-flex;
		align-items: center;
		gap: 3px;
		padding: 2px;
		border-radius: 4px;
		color: inherit;
		transition: opacity 0.12s;
	}
	.assistant-message-action:hover {
		opacity: 1;
		background: color-mix(in srgb, currentColor 14%, transparent);
	}
	.assistant-message-action:disabled {
		cursor: not-allowed;
		opacity: 0.4;
	}
	.assistant-file-input {
		display: none;
	}
	:global(.assistant-markdown .assistant-code pre),
	:global(.assistant-markdown .assistant-code code) {
		padding: 0;
		border-radius: 0;
		background: none;
	}
	.assistant-attachment {
		display: block;
		max-width: 100%;
		margin-top: 6px;
		border: 1px solid var(--ds-border);
		border-radius: 6px;
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
		display: flex;
		align-items: center;
		gap: 8px;
		margin: 0;
		padding: 8px 14px;
		border-top: 1px solid var(--ds-danger);
		background: var(--ds-danger-dim);
		font-size: 12px;
		color: var(--ds-danger);
	}
	.assistant-error button {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		flex: none;
		margin-left: auto;
		padding: 2px 6px;
		border: 1px solid currentColor;
		border-radius: 6px;
		font-size: 11px;
		color: inherit;
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
