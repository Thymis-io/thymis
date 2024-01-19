<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();

	let tags: string[] = [];
	let availableTags: string[];

	$: tags = $modalStore[0]?.meta.tags;
	$: availableTags = $modalStore[0]?.meta.availableTags;

	function toggle(tag: string) {
		if (tags.includes(tag)) {
			tags = tags.filter((t) => t !== tag);
		} else {
			tags = [...tags, tag];
		}
	}

	function onSubmit(): void {
		if ($modalStore[0].response) {
			$modalStore[0].response(tags);
		}
		modalStore.close();
	}
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-4">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<div class="flex flex-wrap gap-2">
			{#each availableTags as availableTag}
				<button
					class="chip {tags.includes(availableTag) ? 'variant-filled' : 'variant-soft'}"
					on:click={() => {
						toggle(availableTag);
					}}
				>
					{availableTag}
				</button>
			{/each}
		</div>
		<footer class="modal-footer {parent.regionFooter}">
			<button class="btn {parent.buttonNeutral}" on:click={parent.onClose}
				>{parent.buttonTextCancel}</button
			>
			<button class="btn {parent.buttonPositive}" on:click={onSubmit}>Save</button>
		</footer>
	</div>
{/if}
