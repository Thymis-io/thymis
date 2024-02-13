<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';

	import { buildStatus } from '$lib/buildstatus';
	export let parent: SvelteComponent;

	//
	let log = '';
	$: {
		// if ($modalStore[0].meta.log == 'stderr' && $buildStatus) {
		if (
			$modalStore &&
			$modalStore.length > 0 &&
			$modalStore[0].meta.log == 'stderr' &&
			$buildStatus
		) {
			log = $buildStatus?.stderr;
		}
		if (
			$modalStore &&
			$modalStore.length > 0 &&
			$modalStore[0].meta.log == 'stdout' &&
			$buildStatus
		) {
			log = $buildStatus?.stdout;
		}
	}
	const modalStore = getModalStore();
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4 w-modal-wide">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<div class="overflow-auto h-80v">
			<pre class="">{log}</pre>
		</div>
	</div>
{/if}
