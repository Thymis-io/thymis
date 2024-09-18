<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { type Device, saveState, state, type Tag } from '$lib/state';
	import {
		Button,
		Input,
		Table,
		TableBodyCell,
		TableHead,
		TableHeadCell,
		Label,
		Helper
	} from 'flowbite-svelte';
	import Trash from 'lucide-svelte/icons/trash';
	import Plus from 'lucide-svelte/icons/plus';
	import Pen from 'lucide-svelte/icons/pen';
	import GripVertical from 'lucide-svelte/icons/grip-vertical';
	import { dndzone, SOURCES, TRIGGERS, type DndEvent } from 'svelte-dnd-action';
	import { flip } from 'svelte/animate';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { KeyboardEventHandler, MouseEventHandler, TouchEventHandler } from 'svelte/elements';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { nameToIdentifier, nameValidation } from '$lib/nameValidation';

	$: tags = $state.tags.map((t) => ({ id: t.identifier, data: t }));
	$: projectTags = $state.tags;
	$: projectTagIds = projectTags.map((t) => t.identifier);

	let newTag = '';

	const flipDurationMs = 200;
	let dragDisabled = true;

	const addTag = (newTag: string) => {
		const newIdentifier = nameToIdentifier(newTag);

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

			saveState();
		}
	};

	const removeTag = (tag: string) => {
		$state.tags = projectTags.filter((t) => t.identifier !== tag);

		$state.devices = $state.devices.map((d) => {
			d.tags = d.tags.filter((t) => t !== tag);
			return d;
		});

		saveState();
	};

	const renameTag = (oldTagIdentifier: string, newTag: string) => {
		const newIdentifier = nameToIdentifier(newTag);

		if (newTag && !projectTagIds.includes(newIdentifier)) {
			$state.tags = projectTags.map((t) => {
				if (t.identifier === oldTagIdentifier) {
					t.displayName = newTag;
					t.identifier = newIdentifier;
				}
				return t;
			});

			$state.devices = $state.devices.map((d) => {
				d.tags = d.tags.map((t) => (t === oldTagIdentifier ? newIdentifier : t));
				return d;
			});

			saveState();
			return true;
		}

		return false;
	};

	const handleConsider = (e: CustomEvent<DndEvent<{ id: string; data: Tag }>>) => {
		const {
			items: newItems,
			info: { source, trigger }
		} = e.detail;
		tags = newItems;
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
	};

	const handleFinalize = (e: CustomEvent<DndEvent<{ id: string; data: Tag }>>) => {
		const {
			items: newItems,
			info: { source, trigger }
		} = e.detail;
		tags = newItems;
		$state.tags = tags.map((t) => t.data);
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
	};

	const startDrag = ((e: MouseEvent | TouchEvent) => {
		// preventing default to prevent lag on touch devices (because of the browser checking for screen scrolling)
		e.preventDefault();
		dragDisabled = false;
	}) satisfies TouchEventHandler<HTMLDivElement> & MouseEventHandler<HTMLDivElement>;

	const handleKeyDown = ((e: KeyboardEvent) => {
		if ((e.key === 'Enter' || e.key === ' ') && dragDisabled) dragDisabled = false;
	}) satisfies KeyboardEventHandler<HTMLDivElement>;
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">Tags</h1>
	<DeployActions />
</div>

<Table shadow>
	<TableHead>
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('devices.table.name')}</TableHeadCell>
		<TableHeadCell padding="p-2" />
		<TableHeadCell padding="p-2">{$t('devices.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody
		use:dndzone={{ items: tags, dragDisabled, flipDurationMs }}
		on:consider={handleConsider}
		on:finalize={handleFinalize}
	>
		{#each tags as tag (tag.id)}
			{@const displayName = tag.data.displayName}
			<tr
				class="border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
				animate:flip={{ duration: flipDurationMs }}
			>
				<TableBodyCell tdClass="p-2">
					<div class="flex items justify-center">
						<div
							tabindex={dragDisabled ? 0 : -1}
							aria-label="drag-handle"
							role="button"
							class="handle"
							style={dragDisabled ? 'cursor: grab' : 'cursor: grabbing'}
							on:mousedown={startDrag}
							on:touchstart={startDrag}
							on:keydown={handleKeyDown}
						>
							<GripVertical size="20" />
						</div>
					</div>
				</TableBodyCell>
				<TableBodyEditCell
					value={displayName}
					onEnter={(value) => {
						const success = renameTag(tag.data.identifier, value);

						if (!success) {
							// Reset the display name if the rename was unsuccessful
							tag.data.displayName = tag.data.displayName;
						}
					}}
				>
					<svelte:fragment slot="bottom" let:value={newTagDisplayName}>
						{#if nameValidation(newTagDisplayName, 'tag')}
							{#if newTagDisplayName !== displayName}
								<Helper color="red">{nameValidation(newTagDisplayName, 'tag')}</Helper>
							{/if}
						{:else}
							<Helper color="green">
								{$t('create-device.name-helper', {
									values: { identifier: nameToIdentifier(newTagDisplayName) }
								})}
							</Helper>
						{/if}
					</svelte:fragment>
				</TableBodyEditCell>
				<TableBodyCell tdClass="p-2" />
				<TableBodyCell tdClass="p-2">
					<Button
						size="sm"
						color="alternative"
						class="p-3 py-1.5 gap-2"
						href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag.data.identifier)}`}
					>
						<Pen />
						{$t('tags.actions.edit')}
					</Button>
					<Button
						size="sm"
						color="alternative"
						on:click={() => removeTag(tag.data.identifier)}
						class="ml-8 p-3 py-1.5 gap-2"
					>
						<Trash />
						{$t('tags.actions.delete')}
					</Button>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>

<div class="flex gap-2 mt-8">
	<Label for="display-name">
		{$t('create-device.display-name-tag')}
		<Input
			id="display-name"
			bind:value={newTag}
			on:keydown={(e) => {
				if (!nameValidation(newTag, 'tag') && e.key === 'Enter') {
					addTag(newTag);
					newTag = '';
				}
			}}
		/>
		{#if newTag !== ''}
			{#if nameValidation(newTag, 'tag')}
				<Helper color="red">{nameValidation(newTag, 'tag')}</Helper>
			{:else}
				<Helper color="green"
					>{$t('create-device.name-helper', {
						values: { identifier: nameToIdentifier(newTag) }
					})}
				</Helper>
			{/if}
		{/if}
	</Label>
	<Button
		on:click={() => {
			addTag(newTag);
			newTag = '';
		}}
		disabled={!!nameValidation(newTag, 'tag')}
		color="alternative"
		class="p-2 gap-2 mt-5"
	>
		<Plus />
		{$t('tags.actions.add')}
	</Button>
</div>
