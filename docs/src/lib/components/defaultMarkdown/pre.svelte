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
		   timeout = setTimeout(() => copied = false, 1500);
	   }
   }
</script>
<div class="relative group">
	<button
		class="absolute top-2 right-2 z-10 px-3 py-2 text-sm rounded bg-white/80 text-gray-500 hover:bg-white/90 active:bg-white border border-gray-200 transition pointer-events-auto cursor-pointer flex items-center gap-2 shadow-sm opacity-0 group-hover:opacity-100 focus:opacity-100"
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
