<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Tag } from '$lib/state';
	import { Button, Table, TableBodyCell, TableHead, TableHeadCell, Helper } from 'flowbite-svelte';
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
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import CreateTagModal from './CreateTagModal.svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	type DraggableTag = { id: string; data: Tag };
	let tags = $state<DraggableTag[]>(
		data.globalState.tags.map((t) => ({ id: t.identifier, data: t }))
	);
	$effect(() => {
		tags = data.globalState.tags.map((t) => ({ id: t.identifier, data: t }));
	});

	let projectTags = $derived(data.globalState.tags);
	let projectTagIds = $derived(projectTags.map((t) => t.identifier));

	let deleteTag: Tag | undefined = $state(undefined);
	let createTagModalOpen = $state(false);

	const flipDurationMs = 200;
	let dragDisabled = $state(true);

	const removeTag = (tag: string) => {
		data.globalState.tags = projectTags.filter((t) => t.identifier !== tag);
		data.globalState.configs = data.globalState.configs.map((config) => {
			config.tags = config.tags.filter((t) => t !== tag);
			return config;
		});

		saveState(data.globalState);
	};

	const renameTag = (oldTagIdentifier: string, newTag: string) => {
		const newIdentifier = nameToIdentifier(newTag);

		if (newTag && !projectTagIds.includes(newIdentifier)) {
			data.globalState.tags = projectTags.map((t) => {
				if (t.identifier === oldTagIdentifier) {
					t.displayName = newTag;
					t.identifier = newIdentifier;
				}
				return t;
			});

			data.globalState.configs = data.globalState.configs.map((config) => {
				config.tags = config.tags.map((t) => (t === oldTagIdentifier ? newIdentifier : t));
				return config;
			});

			saveState(data.globalState);
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
		data.globalState.tags = tags.map((t) => t.data);
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
	};

	const startDrag = ((e: MouseEvent | TouchEvent) => {
		// preventing default to prevent lag on touch tags (because of the browser checking for screen scrolling)
		e.preventDefault();
		dragDisabled = false;
	}) satisfies TouchEventHandler<HTMLDivElement> & MouseEventHandler<HTMLDivElement>;

	const handleKeyDown = ((e: KeyboardEvent) => {
		if ((e.key === 'Enter' || e.key === ' ') && dragDisabled) dragDisabled = false;
	}) satisfies KeyboardEventHandler<HTMLDivElement>;
</script>

<PageHead
	title={$t('nav.tags')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
>
	<Button
		color="alternative"
		class="whitespace-nowrap gap-2 px-2 py-1 m-1"
		on:click={() => (createTagModalOpen = true)}
	>
		<Plus size={20} />
		{$t('tags.actions.create')}
	</Button>
</PageHead>
<DeleteConfirm
	target={deleteTag?.displayName}
	on:confirm={() => {
		if (deleteTag) {
			removeTag(deleteTag.identifier);
			deleteTag = undefined;
		}
	}}
	on:cancel={() => (deleteTag = undefined)}
/>
<CreateTagModal globalState={data.globalState} bind:open={createTagModalOpen} />
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('tags.table.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('tags.table.configs')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('tags.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody
		use:dndzone={{ items: tags, dragDisabled, flipDurationMs }}
		onconsider={handleConsider}
		onfinalize={handleFinalize}
	>
		{#each tags as tag (tag.id)}
			{@const displayName = tag.data.displayName}
			<tr
				class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
				animate:flip={{ duration: flipDurationMs }}
			>
				<TableBodyCell tdClass="p-2">
					<div class="flex items-center justify-center">
						<div
							tabindex={dragDisabled ? 0 : -1}
							aria-label="drag-handle"
							role="button"
							class="handle"
							style={dragDisabled ? 'cursor: grab' : 'cursor: grabbing'}
							onmousedown={startDrag}
							ontouchstart={startDrag}
							onkeydown={handleKeyDown}
						>
							<GripVertical size={'1rem'} class="min-w-4" />
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
					{#snippet bottom({ value: newTagDisplayName })}
						{#if nameValidation(data.globalState, newTagDisplayName, 'tag')}
							{#if newTagDisplayName !== displayName}
								<Helper color="red">
									{nameValidation(data.globalState, newTagDisplayName, 'tag')}
								</Helper>
							{/if}
						{:else}
							<Helper color="green">
								{$t('create-configuration.name-helper-tag', {
									values: { identifier: nameToIdentifier(newTagDisplayName) }
								})}
							</Helper>
						{/if}
					{/snippet}
					{#snippet children()}
						<IdentifierLink
							identifier={tag.data.identifier}
							context="tag"
							globalState={data.globalState}
						/>
					{/snippet}
				</TableBodyEditCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					{@const configsWithTag = data.globalState.configs.filter((config) =>
						config.tags.includes(tag.data.identifier)
					)}
					<div class="flex flex-wrap gap-2">
						{#each configsWithTag as config}
							<IdentifierLink
								identifier={config.identifier}
								context="config"
								globalState={data.globalState}
								solidBackground
							/>
						{/each}
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-1">
					<Button
						size="sm"
						color="alternative"
						class="p-3 py-1.5 gap-2"
						href={`/configuration/edit?${buildGlobalNavSearchParam(data.globalState, $page.url.search, 'tag', tag.data.identifier)}`}
					>
						<Pen size={18} />
						{$t('tags.actions.edit')}
					</Button>
					<Button
						size="sm"
						color="alternative"
						on:click={() => (deleteTag = tag.data)}
						class="ml-8 p-3 py-1.5 gap-2"
					>
						<Trash size={18} />
						{$t('tags.actions.delete')}
					</Button>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
