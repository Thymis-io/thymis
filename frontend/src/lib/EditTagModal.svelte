<script lang="ts">
	import { t } from 'svelte-i18n';
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
		if (newTag && !availableTags.find((t) => t.displayName === newTag)) {
			availableTags = [
				...availableTags,
				{
					displayName: newTag,
					identifier: newTag.toLocaleLowerCase().replaceAll(' ', '-'),
					priority: 5,
					modules: []
				}
			];
		}

		newTag = '';
	}

	const removeTag = (tag: string) => {
		tags = tags.filter((t) => t !== tag);
		availableTags = availableTags.filter((t) => t.identifier !== tag);
	};
</script>

<Modal title={$t('devices.edit-tags-title')} bind:open outsideclose>
	<div class="flex flex-wrap gap-2">
		{#each availableTags as availableTag}
			<Button
				rounded
				color={tags.includes(availableTag.displayName) ? 'primary' : 'alternative'}
				class={tags.includes(availableTag.displayName)
					? 'px-[15px] py-[11px]'
					: 'px-[14px] py-[10px]'}
				on:click={() => {
					toggle(availableTag.displayName);
				}}
			>
				{availableTag.displayName}
				<Button
					color="red"
					size="xs"
					class="ml-6 p-1"
					on:click={() => removeTag(availableTag.identifier)}
				>
					<Minus size="12" />
				</Button>
			</Button>
			<!-- remove button -->
		{/each}
	</div>
	<div class="flex gap-2">
		<Input
			type="text"
			class="input"
			placeholder={$t('devices.new-tag-placeholder')}
			bind:value={newTag}
		/>
		<button class="btn btn-sm variant-filled" on:click={() => addTag()}>
			<Plus />
		</button>
	</div>
	<div class="flex justify-end gap-2">
		<Button color="alternative" on:click={() => onClose?.()}>{$t('common.cancel')}</Button>
		<Button
			on:click={() => {
				onSave?.(tags, availableTags);
				onClose?.();
			}}
		>
			{$t('common.save')}
		</Button>
	</div>
</Modal>
