<script lang="ts">
	let props = $props();

	let copied = $state(false);
	let timeout: ReturnType<typeof setTimeout> | null = null;
	let codeRef: HTMLPreElement;

	function copyCode() {
		if (props.code) {
			navigator.clipboard.writeText(props.code);
			copied = true;
			if (timeout) clearTimeout(timeout);
			timeout = setTimeout(() => (copied = false), 1500);
		}
	}
</script>

<div class="group relative">
	<button
		class="pointer-events-auto absolute right-2 top-2 z-10 flex cursor-pointer items-center gap-2 rounded border border-gray-200 bg-white/80 px-3 py-2 text-sm text-gray-500 opacity-0 shadow-sm transition hover:bg-white/90 focus:opacity-100 active:bg-white group-hover:opacity-100"
		style="backdrop-filter: blur(1px);"
		onclick={copyCode}
		aria-label="Copy code"
		type="button"
		tabindex="0"
	>
		{#if copied}
			<span class="font-medium text-green-500">Copied!</span>
		{:else}
			<span class="font-medium">Copy</span>
		{/if}
		<i class="fa fa-copy text-base"></i>
	</button>
	<pre bind:this={codeRef} class="{props.class} not-prose">{@render props.children()}</pre>
</div>
