<script lang="ts">
	import Plus from 'lucide-svelte/icons/plus';
	import Minus from 'lucide-svelte/icons/minus';
	import type { Tag } from '$lib/state';
	import { Button, Modal, Input } from 'flowbite-svelte';

	export let open: boolean;
	export let onClose: (() => void) | undefined = undefined;
	export let onSave: ((tags: string[], availableTags: Tag[]) => void) | undefined = undefined;

	export let tags: string[];
	export let availableTags: Tag[];
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

	const removeTag = (tag: string) => {
		tags = tags.filter((t) => t !== tag);
		availableTags = availableTags.filter((t) => t.name !== tag);
	};
</script>

<Modal title="Edit Tags" bind:open>
	<div class="flex flex-wrap gap-2">
		{#each availableTags as availableTag}
			<Button
				rounded
				color={tags.includes(availableTag.name) ? 'primary' : 'alternative'}
				class={tags.includes(availableTag.name) ? 'px-[15px] py-[11px]' : 'px-[14px] py-[10px]'}
				on:click={() => {
					toggle(availableTag.name);
				}}
			>
				{availableTag.name}
				<Button
					color="red"
					size="xs"
					class="ml-6 p-1"
					on:click={() => removeTag(availableTag.name)}
				>
					<Minus size="12" />
				</Button>
			</Button>
			<!-- remove button -->
		{/each}
	</div>
	<div class="flex gap-2">
		<Input type="text" class="input" placeholder="New Tag" bind:value={newTag} />
		<button class="btn btn-sm variant-filled" on:click={() => addTag()}>
			<Plus />
		</button>
	</div>
	<div class="flex justify-end gap-2">
		<Button color="alternative" on:click={() => onClose?.()}>Cancel</Button>
		<Button
			on:click={() => {
				onSave?.(tags, availableTags);
				onClose?.();
			}}
		>
			Save
		</Button>
	</div>
</Modal>
