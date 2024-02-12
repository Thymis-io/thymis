<script lang="ts">
	import type { SvelteComponent } from 'svelte';
	import { getModalStore } from '@skeletonlabs/skeleton';
	// import { Plus } from 'lucide-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import type { Tag } from '$lib/state';

	export let parent: SvelteComponent;
	const modalStore = getModalStore();

	let tags: string[] = $modalStore[0]?.meta.tags;
	let availableTags: Tag[] = $modalStore[0]?.meta.availableTags;
	let newTag = '';

	function toggle(tag: string) {
		if (tags.includes(tag)) {
			tags = tags.filter((t) => t !== tag);
		} else {
			tags = [...tags, tag];
		}
	}

	function addTag() {
		if (newTag && !availableTags.find((t) => t.name === newTag)) {
			availableTags = [...availableTags, { name: newTag, priority: 5, modules: [] }];
		}

		newTag = '';
	}

	function onSubmit(): void {
		if ($modalStore[0].response) {
			$modalStore[0].response({ deviceTags: tags, availableTags: availableTags });
		}
		modalStore.close();
	}
</script>

{#if $modalStore[0]}
	<div class="modal-example-form card p-4 w-modal shadow-xl space-y-8">
		<header class="text-2xl font-bold">{$modalStore[0].title ?? '(title missing)'}</header>
		<div class="flex flex-wrap gap-2">
			{#each availableTags as availableTag}
				<button
					class="chip {tags.includes(availableTag.name) ? 'variant-filled' : 'variant-soft'}"
					on:click={() => {
						toggle(availableTag.name);
					}}
				>
					{availableTag.name}
				</button>
			{/each}
		</div>
		<div class="flex gap-2">
			<input type="text" class="input" placeholder="New Tag" bind:value={newTag} />
			<button class="btn btn-sm variant-filled" on:click={() => addTag()}>
				<Plus />
			</button>
		</div>
		<footer class="modal-footer {parent.regionFooter}">
			<button class="btn {parent.buttonNeutral}" on:click={parent.onClose}
				>{parent.buttonTextCancel}</button
			>
			<button class="btn {parent.buttonPositive}" on:click={onSubmit}>Save</button>
		</footer>
	</div>
{/if}
