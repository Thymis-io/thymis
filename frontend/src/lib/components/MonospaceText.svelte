<script lang="ts">
	import { t } from 'svelte-i18n';
	import Copy from 'lucide-svelte/icons/copy';
	import { HighlightAuto, LineNumbers, Highlight } from 'svelte-highlight';
	import type { LanguageType } from 'svelte-highlight/languages';
	import ashes from 'svelte-highlight/styles/ashes';

	export let code: string;
	export let language: LanguageType<string> | undefined = undefined;

	let copied = false;

	const copy = () => {
		navigator.clipboard.writeText(code);
		copied = true;
		setTimeout(() => {
			copied = false;
		}, 3000);
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
		<Highlight {code} {language} let:highlighted>
			<LineNumbers {highlighted} />
		</Highlight>
	{:else}
		<HighlightAuto {code} let:highlighted>
			<LineNumbers {highlighted} />
		</HighlightAuto>
	{/if}
	<div class="absolute top-2 right-2">
		<button
			class="absolute right-0 flex items-center gap-2 z-20 text-white hover:bg-gray-700 rounded-md p-1 w-max h-max opacity-30 hover:opacity-100"
			on:click={copy}
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
