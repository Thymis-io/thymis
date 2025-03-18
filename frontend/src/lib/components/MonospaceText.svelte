<script lang="ts">
	import { t } from 'svelte-i18n';
	import Copy from 'lucide-svelte/icons/copy';
	// import { HighlightAuto, LineNumbers, Highlight } from 'svelte-highlight';
	// import HighlightAuto from 'svelte-highlight/HighlightAuto.svelte';
	import Highlight from 'svelte-highlight/Highlight.svelte';
	import LineNumbers from 'svelte-highlight/LineNumbers.svelte';
	import type { LanguageType } from 'svelte-highlight/languages';
	import type HighlightAutoType from 'svelte-highlight/HighlightAuto.svelte';
	import ashes from 'svelte-highlight/styles/ashes';

	interface Props {
		code: string;
		language?: LanguageType<string> | undefined;
	}

	let { code, language = undefined }: Props = $props();

	let copied = $state(false);

	const copy = () => {
		navigator.clipboard.writeText(code);
		copied = true;
		setTimeout(() => {
			copied = false;
		}, 3000);
	};

	// only import HighlightAuto if needed
	let hightlightAuto: HighlightAutoType | null = null;
	const getHighlightAuto = async () => {
		if (!hightlightAuto) {
			const { default: HighlightAuto } = await import('svelte-highlight/HighlightAuto.svelte');
			hightlightAuto = HighlightAuto;
		}
		if (!hightlightAuto) {
			throw new Error('Failed to load HighlightAuto');
		}
		return hightlightAuto;
	};
</script>

<svelte:head>
	{@html ashes}
</svelte:head>

<div class="relative">
	{#if code.length > 5000}
		<!-- Code highlighting is very expensive, disable it after an arbitrary number of characters -->
		<LineNumbers highlighted={code} />
	{:else if language}
		<Highlight {code} {language}>
			{#snippet children({ highlighted })}
				<LineNumbers {highlighted} />
			{/snippet}
		</Highlight>
	{:else}
		{#await getHighlightAuto()}
			<!-- load -->
			<div class="flex items-center justify-center h-full">
				<svg
					class="animate-spin h-5 w-5 text-gray-200"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
				>
					<path
						fill="currentColor"
						d="M12 2a10 10 0 1 0 0 20a10 10 0 0 0 0-20zm1.5 15h-3v-2h3v2zm0-4h-3V7h3v6z"
					/>
				</svg>
			</div>
		{:then HighlightAuto}
			<HighlightAuto {code}>
				{#snippet children({ highlighted })}
					<LineNumbers {highlighted} />
				{/snippet}
			</HighlightAuto>
		{:catch error}
			<!-- handle error -->
			<div class="text-red-500">
				Error loading code: {error.message}
			</div>
		{/await}
	{/if}
	<div class="absolute top-2 right-2">
		<button
			class="absolute right-0 flex items-center gap-2 z-20 text-white hover:bg-gray-700 rounded-md p-1 w-max h-max opacity-30 hover:opacity-100"
			onclick={copy}
		>
			<Copy class="w-5 h-5" />
			{#if copied}
				{$t('codeblock.copied')}
			{:else}
				{$t('codeblock.copy')}
			{/if}
		</button>
	</div>
</div>
