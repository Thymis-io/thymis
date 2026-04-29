<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { t } from 'svelte-i18n';
	import { fetchWithNotify } from '$lib/fetchWithNotify';

	import Send from 'lucide-svelte/icons/send-horizontal';
	import Bot from 'lucide-svelte/icons/bot';
	import User from 'lucide-svelte/icons/user';
	import AlertTriangle from 'lucide-svelte/icons/alert-triangle';
	import Sparkles from 'lucide-svelte/icons/sparkles';

	interface ChatMessage {
		role: 'user' | 'assistant';
		content: string;
		isPartial?: boolean;
	}

	let messages: ChatMessage[] = $state([]);
	let userInput = $state('');
	let isLoading = $state(false);
	let aiStatus = $state<{ enabled: boolean; api_key_configured: boolean } | null>(null);
	let error = $state<string | null>(null);
	let chatEndRef: HTMLDivElement | null = $state(null);

	const chatController = { abort: null as AbortController | null };

	onMount(async () => {
		try {
			const res = await fetchWithNotify('/api/ai-assistant/status');
			aiStatus = await res.json();
		} catch (e) {
			error = 'Failed to check AI assistant status';
			console.error(e);
		}
	});

	const scrollToBottom = () => {
		if (chatEndRef) {
			chatEndRef.scrollIntoView({ behavior: 'smooth' });
		}
	};

	onMount(() => scrollToBottom());

	const sendMessage = async () => {
		const text = userInput.trim();
		if (!text || isLoading) return;

		messages = [...messages, { role: 'user', content: text }];
		userInput = '';
		scrollToBottom();

		isLoading = true;
		error = null;

		const assistantMsg: ChatMessage = { role: 'assistant', content: '', isPartial: true };
		messages = [...messages, assistantMsg];

		try {
			const abortController = new AbortController();
			chatController.abort = abortController;

			const response = await fetch('/api/ai-assistant/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					messages: messages
						.filter((m) => !m.isPartial)
						.map((m) => ({
							role: m.role,
							content: m.content
						})),
					stream: true
				}),
				signal: abortController.signal
			});

			if (!response.ok) {
				const errText = await response.text();
				throw new Error(`API error ${response.status}: ${errText}`);
			}

			const reader = response.body?.getReader();
			if (!reader) throw new Error('No response body');

			const decoder = new TextDecoder();
			let buffer = '';

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (!line.startsWith('data: ')) continue;
					const data = line.slice(6);

					if (data === '[DONE]') {
						assistantMsg.isPartial = false;
						continue;
					}

					try {
						const parsed = JSON.parse(data);
						if (parsed.content) {
							assistantMsg.content += parsed.content;
							scrollToBottom();
						}
					} catch {
						// Skip non-JSON SSE lines
					}
				}
			}
		} catch (e) {
			if (e instanceof DOMException && e.name === 'AbortError') return;
			error = e instanceof Error ? e.message : 'Unknown error';
			assistantMsg.isPartial = false;
		} finally {
			isLoading = false;
			chatController.abort = null;
			scrollToBottom();
		}
	};

	const stopGeneration = () => {
		chatController.abort?.abort();
		chatController.abort = null;
		isLoading = false;
		// Mark the partial message as complete
		const lastMsg = messages[messages.length - 1];
		if (lastMsg?.isPartial) {
			lastMsg.isPartial = false;
		}
	};

	const handleKeydown = (e: KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	};

	const clearChat = () => {
		messages = [];
		error = null;
	};

	onDestroy(() => {
		chatController.abort?.abort();
	});
</script>

<div class="flex flex-col h-full max-w-4xl mx-auto">
	<!-- Header -->
	<div class="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
		<div class="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
			<Sparkles class="w-5 h-5 text-blue-600 dark:text-blue-400" />
		</div>
		<div class="flex-1">
			<h1 class="text-lg font-semibold text-gray-900 dark:text-white">{$t('nav.ai-assistant')}</h1>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				{aiStatus?.enabled
					? aiStatus.api_key_configured
						? 'Connected — Ready to help'
						: 'Connected — No API key configured'
					: 'AI Assistant disabled'}
			</p>
		</div>
		{#if messages.length > 0}
			<button
				onclick={clearChat}
				class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
			>
				Clear
			</button>
		{/if}
	</div>

	<!-- Status warnings -->
	{#if !aiStatus?.enabled}
		<div
			class="mx-4 mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 flex items-start gap-2"
		>
			<AlertTriangle class="w-4 h-4 text-yellow-600 dark:text-yellow-400 mt-0.5 shrink-0" />
			<div>
				<p class="text-sm font-medium text-yellow-800 dark:text-yellow-300">
					AI Assistant Disabled
				</p>
				<p class="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
					Set <code class="font-mono text-xs bg-yellow-100 dark:bg-yellow-900/40 px-1 rounded"
						>THYMIS_AI_ASSISTANT_ENABLED=true</code
					> in your environment to enable.
				</p>
			</div>
		</div>
	{:else if aiStatus?.enabled && !aiStatus.api_key_configured}
		<div
			class="mx-4 mt-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 flex items-start gap-2"
		>
			<AlertTriangle class="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
			<div>
				<p class="text-sm font-medium text-amber-800 dark:text-amber-300">API Key Not Configured</p>
				<p class="text-xs text-amber-700 dark:text-amber-400 mt-1">
					Set <code class="font-mono text-xs bg-amber-100 dark:bg-amber-900/40 px-1 rounded"
						>THYMIS_AI_ASSISTANT_API_KEY</code
					> to use the assistant.
				</p>
			</div>
		</div>
	{/if}

	<!-- Error -->
	{#if error}
		<div
			class="mx-4 mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-start gap-2"
		>
			<AlertTriangle class="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
			<p class="text-sm text-red-800 dark:text-red-300">{error}</p>
		</div>
	{/if}

	<!-- Chat messages -->
	<div class="flex-1 overflow-y-auto px-4 py-4 space-y-4">
		{#if messages.length === 0}
			<div class="flex flex-col items-center justify-center h-full text-center py-12">
				<Bot class="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
				<p class="text-gray-500 dark:text-gray-400 text-sm">
					Ask me anything about your Thymis configuration, modules, or deployments.
				</p>
				<div class="mt-4 space-y-2">
					<button
						onclick={() => {
							userInput = 'How do I configure a Raspberry Pi 4 as a Kiosk?';
						}}
						class="block text-left text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
					>
						"How do I configure a Raspberry Pi 4 as a Kiosk?"
					</button>
					<button
						onclick={() => {
							userInput = 'What modules are available for device configuration?';
						}}
						class="block text-left text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
					>
						"What modules are available for device configuration?"
					</button>
					<button
						onclick={() => {
							userInput = 'How do I add a custom NixOS module?';
						}}
						class="block text-left text-xs text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800"
					>
						"How do I add a custom NixOS module?"
					</button>
				</div>
			</div>
		{/if}

		{#each messages as message (message.role + message.content)}
			<div class="flex gap-3 {message.role === 'user' ? 'flex-row-reverse' : ''}">
				<!-- Avatar -->
				<div class="shrink-0 mt-1">
					{#if message.role === 'user'}
						<div
							class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center"
						>
							<User class="w-4 h-4 text-blue-600 dark:text-blue-400" />
						</div>
					{:else}
						<div
							class="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center"
						>
							<Bot class="w-4 h-4 text-green-600 dark:text-green-400" />
						</div>
					{/if}
				</div>

				<!-- Message bubble -->
				<div
					class="max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-words {message.role ===
					'user'
						? 'bg-blue-600 text-white'
						: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'}"
				>
					{message.content || (message.isPartial ? '...' : '')}
					{#if message.isPartial}
						<span class="inline-block w-1.5 h-4 ml-1 bg-gray-400 dark:bg-gray-500 animate-pulse"
						></span>
					{/if}
				</div>
			</div>
		{/each}

		<!-- Loading indicator -->
		{#if isLoading && messages.length === 0}
			<div class="flex gap-3">
				<div
					class="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center shrink-0"
				>
					<Bot class="w-4 h-4 text-green-600 dark:text-green-400" />
				</div>
				<div
					class="max-w-[80%] rounded-xl px-4 py-3 bg-gray-100 dark:bg-gray-800 flex gap-1.5 items-center"
				>
					<span class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0ms"
					></span>
					<span
						class="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
						style="animation-delay: 150ms"
					></span>
					<span
						class="w-2 h-2 rounded-full bg-gray-400 animate-bounce"
						style="animation-delay: 300ms"
					></span>
				</div>
			</div>
		{/if}

		<div bind:this={chatEndRef}></div>
	</div>

	<!-- Input area -->
	<div class="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
		<div class="flex gap-2 max-w-4xl mx-auto">
			<textarea
				bind:value={userInput}
				onkeydown={handleKeydown}
				disabled={isLoading || !aiStatus?.enabled}
				placeholder="Ask about your Thymis project..."
				rows={1}
				class="flex-1 resize-none rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-colors"
				oninput={(e: Event) => {
					const target = e.target as HTMLTextAreaElement;
					target.style.height = 'auto';
					target.style.height = Math.min(target.scrollHeight, 160) + 'px';
				}}
			></textarea>
			{#if isLoading}
				<button
					onclick={stopGeneration}
					class="shrink-0 px-4 py-3 rounded-xl bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
					title="Stop generation"
				>
					<svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
						<rect x="6" y="6" width="12" height="12" rx="2" />
					</svg>
				</button>
			{:else}
				<button
					onclick={sendMessage}
					disabled={!userInput.trim() || !aiStatus?.enabled}
					class="shrink-0 px-4 py-3 rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400 transition-colors disabled:cursor-not-allowed"
				>
					<Send class="w-5 h-5" />
				</button>
			{/if}
		</div>
		<p class="text-xs text-gray-400 dark:text-gray-500 text-center mt-2">
			AI can make mistakes. Verify important configurations before deploying.
		</p>
	</div>
</div>

<style lang="postcss">
	:global(.dark) {
		textarea {
			caret-color: white;
		}
	}
</style>
