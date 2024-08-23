<script lang="ts">
	import { t } from 'svelte-i18n';
	import Plus from 'lucide-svelte/icons/plus';
	import Minus from 'lucide-svelte/icons/minus';
	import { type Device, saveState, state, type Tag } from '$lib/state';
	import { Button, Modal, Input } from 'flowbite-svelte';

	export let currentlyEditingDevice: Device | undefined;
	let newTag = '';

	$: projectTags = $state.tags;
	$: projectTagIds = projectTags.map((t) => t.identifier);
	$: deviceTags = currentlyEditingDevice?.tags || [];

	function toggle(tag: string) {
		if (!currentlyEditingDevice) return;
		if (deviceTags?.includes(tag)) {
			currentlyEditingDevice.tags = deviceTags.filter((t) => t !== tag);
		} else {
			currentlyEditingDevice.tags = [...(deviceTags || []), tag];
		}
	}

	function addTag() {
		const newIdentifier = newTag.toLocaleLowerCase().replaceAll(' ', '-');

		if (newTag && !projectTagIds.includes(newIdentifier)) {
			$state.tags = [
				...projectTags,
				{
					displayName: newTag,
					identifier: newIdentifier,
					priority: 90,
					modules: []
				}
			];
		}

		newTag = '';
		saveState();
	}

	const removeTag = (tag: string) => {
		if (!currentlyEditingDevice) return;
		currentlyEditingDevice.tags = deviceTags?.filter((t) => t !== tag);
		$state.tags = projectTags.filter((t) => t.identifier !== tag);
		saveState();
	};
</script>

<Modal
	title={$t('devices.edit-tags-title')}
	open={!!currentlyEditingDevice}
	on:close={() => (currentlyEditingDevice = undefined)}
	outsideclose
>
	<div class="flex flex-wrap gap-2">
		{#each projectTags as availableTag (availableTag.identifier)}
			<Button
				rounded
				color={deviceTags.includes(availableTag.identifier) ? 'primary' : 'alternative'}
				class={deviceTags.includes(availableTag.identifier)
					? 'px-[15px] py-[11px]'
					: 'px-[14px] py-[10px]'}
				on:click={() => {
					toggle(availableTag.identifier);
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
		<Button
			on:click={async () => {
				currentlyEditingDevice = undefined;
				await saveState();
			}}
		>
			{$t('common.save')}
		</Button>
	</div>
</Modal>
