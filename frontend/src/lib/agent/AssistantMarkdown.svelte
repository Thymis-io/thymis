<script lang="ts">
	import DOMPurify from 'dompurify';
	import { marked, type Token, type Tokens } from 'marked';
	import MonospaceText from '$lib/components/MonospaceText.svelte';

	interface Props {
		/** Markdown source of one assistant text part. */
		markdown: string;
		/** False while the part is still streaming, which disables code highlighting. */
		complete: boolean;
	}

	let { markdown, complete }: Props = $props();

	// Block-level tokens let code run through the shared highlighter, while prose
	// keeps rendering as sanitized HTML.
	const blocks = $derived(marked.lexer(markdown));

	const isCodeBlock = (block: Token): block is Tokens.Code => block.type === 'code';

	const renderBlock = (block: Token) => DOMPurify.sanitize(marked.parser([block]));
</script>

{#each blocks as block, index (index)}
	{#if isCodeBlock(block) && complete}
		<div class="assistant-code">
			<MonospaceText code={block.text} />
		</div>
	{:else}
		{@html renderBlock(block)}
	{/if}
{/each}
