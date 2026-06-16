<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Tag } from '$lib/state';
	import { Helper } from 'flowbite-svelte';
	import Trash from 'lucide-svelte/icons/trash';
	import Pen from 'lucide-svelte/icons/pen';
	import Server from 'lucide-svelte/icons/server';
	import GripVertical from 'lucide-svelte/icons/grip-vertical';
	import { SOURCES, TRIGGERS, type DndEvent } from 'svelte-dnd-action';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { KeyboardEventHandler, MouseEventHandler, TouchEventHandler } from 'svelte/elements';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { nameToIdentifier, nameValidation } from '$lib/nameValidation';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import CreateTagModal from './CreateTagModal.svelte';
	import Page from '$lib/components/layout/Page.svelte';
	import CreateButton from '$lib/components/layout/CreateButton.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
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

	// How many deployed devices use a tag = devices whose deployed config carries the tag.
	const deviceCountForTag = (tagIdentifier: string) => {
		const configIdsWithTag = new Set(
			data.globalState.configs
				.filter((config) => config.tags.includes(tagIdentifier))
				.map((config) => config.identifier)
		);
		return data.deploymentInfos.filter(
			(info) => info.deployed_config_id && configIdsWithTag.has(info.deployed_config_id)
		).length;
	};

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

<Page title={$t('nav.tags')} subtitle={$t('tags.subtitle')}>
	{#snippet actions()}
		<CreateButton label={$t('tags.actions.create')} onclick={() => (createTagModalOpen = true)} />
	{/snippet}
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
	<DataTable
		columns={[
			{ class: 'w-12' },
			{ label: $t('tags.table.name') },
			{ label: $t('tags.table.configs') },
			{ label: $t('tags.table.devices') },
			{ label: $t('tags.table.actions'), align: 'right' }
		]}
		rows={tags}
		rowKey={(tag) => tag.id}
		empty={$t('tags.empty')}
		dnd={{ dragDisabled, flipDurationMs, onConsider: handleConsider, onFinalize: handleFinalize }}
	>
		{#snippet row(tag)}
			{@const displayName = tag.data.displayName}
			{@const configsWithTag = data.globalState.configs.filter((config) =>
				config.tags.includes(tag.data.identifier)
			)}
			<td>
				<div class="flex items-center justify-center">
					<div
						tabindex={dragDisabled ? 0 : -1}
						aria-label={$t('common.drag-handle')}
						role="button"
						class="handle"
						style={dragDisabled ? 'cursor: grab' : 'cursor: grabbing'}
						onmousedown={startDrag}
						ontouchstart={startDrag}
						onkeydown={handleKeyDown}
					>
						<GripVertical size={'1rem'} class="min-w-4" style="color: var(--ds-text-mute)" />
					</div>
				</div>
			</td>
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
			<td>
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
			</td>
			{@const deviceCount = deviceCountForTag(tag.data.identifier)}
			<td>
				<span class="ds-count" class:empty={deviceCount === 0}>
					<Server size={14} />
					{deviceCount}
				</span>
			</td>
			<td>
				<RowActions>
					<RowMenu
						label={$t('tags.table.actions')}
						items={[
							{
								label: $t('tags.actions.edit'),
								icon: Pen,
								href: `/configuration/edit?${buildGlobalNavSearchParam(data.globalState, $page.url.search, 'tag', tag.data.identifier)}`
							},
							{
								label: $t('tags.actions.delete'),
								icon: Trash,
								variant: 'danger',
								onclick: () => (deleteTag = tag.data)
							}
						]}
					/>
				</RowActions>
			</td>
		{/snippet}
	</DataTable>
</Page>
