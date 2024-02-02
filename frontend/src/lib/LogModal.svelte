<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4 w-modal-wide">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<div class="overflow-auto h-80v">
			<pre class="">{$modalStore[0].meta.log}</pre>
		</div>
	</div>
{/if}
