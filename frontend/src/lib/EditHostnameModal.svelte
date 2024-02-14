<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';
	// import { Plus } from 'lucide-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import Minus from 'lucide-svelte/icons/minus';
	import type { Tag } from '$lib/state';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();

	let hostname: string = $modalStore[0]?.meta.hostname;

	const onSubmit = () => {
		if ($modalStore[0].response) {
			$modalStore[0].response({ hostname });
		}
		modalStore.close();
	};
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-8">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<div class="flex gap-2">
			<input type="text" class="input" placeholder="Hostname" bind:value={hostname} />
		</div>
		<footer class="modal-footer {parent.regionFooter}">
			<button class="btn {parent.buttonNeutral}" on:click={parent.onClose}
				>{parent.buttonTextCancel}</button
			>
			<button class="btn {parent.buttonPositive}" on:click={onSubmit}>Save</button>
		</footer>
	</div>
{/if}
