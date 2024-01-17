<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';
	import InstallationStepper from '$lib/InstallationStepper.svelte';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();

	function onSubmit(data: any): void {
		if ($modalStore[0].response) {
			$modalStore[0].response(data);
		}
		//modalStore.close();
	}
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<InstallationStepper {onSubmit} />
	</div>
{/if}
