<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Config, type Tag } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import { Button, Table, TableBodyCell, TableHead, TableHeadCell, Tooltip } from 'flowbite-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import Search from 'lucide-svelte/icons/search';
	import Trash from 'lucide-svelte/icons/trash-2';
	import Sliders from 'lucide-svelte/icons/sliders-horizontal';
	import GripVertical from 'lucide-svelte/icons/grip-vertical';
	import CreateConfigModal from './CreateConfigModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { PageData } from '../../devices/$types';
	import { dndzone, SOURCES, TRIGGERS, type DndEvent } from 'svelte-dnd-action';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import type { KeyboardEventHandler, MouseEventHandler, TouchEventHandler } from 'svelte/elements';
	import { flip } from 'svelte/animate';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	const flipDurationMs = 200;
	let dragDisabled = $state(true);

	interface Props {
		data: PageData;
	}

	let { data = $bindable() }: Props = $props();

	type DraggableConfig = { id: string; data: Config };
	let configs = $state<DraggableConfig[]>(
		data.globalState.configs.map((config) => ({ id: config.identifier, data: config }))
	);
	$effect(() => {
		configs = data.globalState.configs.map((config) => ({ id: config.identifier, data: config }));
	});

	const findTag = (identifier: string) => {
		return data.globalState.tags.find((t) => t.identifier === identifier);
	};

	const handleConsider = (e: CustomEvent<DndEvent<{ id: string; data: Config }>>) => {
		const {
			items: newItems,
			info: { source, trigger }
		} = e.detail;
		configs = newItems;
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
	};
	const handleFinalize = (e: CustomEvent<DndEvent<{ id: string; data: Config }>>) => {
		const {
			items: newItems,
			info: { source }
		} = e.detail;
		configs = newItems;
		// also send new config order to backend and reload
		data.globalState.configs = configs.map((config) => config.data);
		saveState(data.globalState);
		// Ensure dragging is stopped on drag finish via pointer (mouse, touch)
		if (source === SOURCES.POINTER) {
			dragDisabled = true;
		}
	};
	const startDrag = ((e) => {
		// preventing default to prevent lag on touch configs (because of the browser checking for screen scrolling)
		e.preventDefault();
		dragDisabled = false;
	}) satisfies TouchEventHandler<HTMLDivElement> & MouseEventHandler<HTMLDivElement>;
	const handleKeyDown = ((e) => {
		if ((e.key === 'Enter' || e.key === ' ') && dragDisabled) dragDisabled = false;
	}) satisfies KeyboardEventHandler<HTMLDivElement>;

	const renameConfig = async (config: Config, displayName: string) => {
		config.displayName = displayName;
		await saveState(data.globalState);
		return true;
	};

	let configToDelete: Config | undefined = $state(undefined);

	const deleteConfiguration = async (config: Config) => {
		const identifier = config.identifier;
		data.globalState.configs = data.globalState.configs.filter(
			(config) => config.identifier !== identifier
		);
		await saveState(data.globalState);
	};

	let newConfigModalOpen = $state(false);
	let currentlyEditingConfig: Config | undefined = $state(undefined);
</script>

<PageHead
	title={$t('configurations.title')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
>
	<Button
		color="alternative"
		class="whitespace-nowrap gap-2 px-2 py-1 m-1"
		on:click={() => (newConfigModalOpen = true)}
		disabled={configs.length >= 5}
	>
		<Plus size={20} />
		{$t('configurations.create-new', {
			values: {
				configCount: configs.length,
				configLimit: 5
			}
		})}
	</Button>
	{#if configs.length >= 5}
		<Tooltip class="z-50 whitespace-pre">
			{$t('configurations.limit-explain', {
				values: {
					configLimit: 5
				}
			})}
		</Tooltip>
	{/if}
</PageHead>
<DeleteConfirm
	target={configToDelete?.displayName}
	on:confirm={() => {
		if (configToDelete) deleteConfiguration(configToDelete);
		configToDelete = undefined;
	}}
	on:cancel={() => (configToDelete = undefined)}
/>
<CreateConfigModal globalState={data.globalState} bind:open={newConfigModalOpen} />
<EditTagModal globalState={data.globalState} bind:currentlyEditingConfig />
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('configurations.table.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('configurations.table.tags')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('configurations.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody
		use:dndzone={{ items: configs, dragDisabled, flipDurationMs }}
		onconsider={handleConsider}
		onfinalize={handleFinalize}
	>
		{#each configs as config (config.id)}
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
					value={config.data.displayName}
					onEnter={async (value) => {
						const success = await renameConfig(config.data, value);

						if (!success) {
							// Reset the display name if the rename was unsuccessful
							config.data.displayName = config.data.displayName;
						}
					}}
				>
					<IdentifierLink
						identifier={config.data.identifier}
						context="config"
						globalState={data.globalState}
					/>
				</TableBodyEditCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex gap-4">
						<div class="flex gap-2">
							{#each config.data.tags as tag, i}
								<IdentifierLink
									identifier={tag}
									context="tag"
									globalState={data.globalState}
									solidBackground
								/>
							{/each}
						</div>
						<button class="p-0" onclick={() => (currentlyEditingConfig = config.data)}>
							<Pen size={'1rem'} class="min-w-4" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-1 px-2 md:px-4">
					<div class="flex gap-2">
						<Button
							class="px-3 py-1.5 gap-2"
							color="alternative"
							href={`/configuration/configuration-details?${buildGlobalNavSearchParam(
								data.globalState,
								$page.url.search,
								'config',
								config.data.identifier
							)}`}
						>
							<Search size={18} class="min-w-3" />
							{$t('configurations.actions.view-details')}
						</Button>
						<Button
							class="px-3 py-1.5 gap-2"
							color="alternative"
							href={`/configuration/edit?${buildGlobalNavSearchParam(
								data.globalState,
								$page.url.search,
								'config',
								config.data.identifier
							)}`}
						>
							<Sliders size={18} class="min-w-3" />
							{$t('nav.configure')}
						</Button>
						<Button
							class="ml-8 px-2 py-1.5 gap-2 justify-start"
							color="alternative"
							on:click={() => (configToDelete = config.data)}
						>
							<Trash size="16" />
							{$t('configurations.actions.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
