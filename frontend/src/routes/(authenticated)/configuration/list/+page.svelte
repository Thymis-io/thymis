<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Config, type Tag } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import { Tooltip } from 'flowbite-svelte';
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
	import Page from '$lib/components/layout/Page.svelte';
	import CreateButton from '$lib/components/layout/CreateButton.svelte';
	import ActionButton from '$lib/components/layout/ActionButton.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
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

<Page title={$t('configurations.title')} subtitle={$t('configurations.subtitle')}>
	{#snippet actions()}
		<CreateButton
			class="disabled:cursor-not-allowed disabled:opacity-50"
			label={$t('configurations.create-new', {
				values: {
					configCount: configs.length,
					configLimit: 5
				}
			})}
			onclick={() => (newConfigModalOpen = true)}
			disabled={configs.length >= 5}
		/>
		{#if configs.length >= 5}
			<Tooltip class="z-50 whitespace-pre">
				{$t('configurations.limit-explain', {
					values: {
						configLimit: 5
					}
				})}
			</Tooltip>
		{/if}
	{/snippet}
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
	<div class="ds-table-wrap">
		<table class="ds-table">
			<thead>
				<tr>
					<th class="w-12"></th>
					<th>{$t('configurations.table.name')}</th>
					<th>{$t('configurations.table.tags')}</th>
					<th class="text-right">{$t('configurations.table.actions')}</th>
				</tr>
			</thead>
			<tbody
				use:dndzone={{ items: configs, dragDisabled, flipDurationMs }}
				onconsider={handleConsider}
				onfinalize={handleFinalize}
			>
				{#each configs as config (config.id)}
					<tr animate:flip={{ duration: flipDurationMs }}>
						<td>
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
									<GripVertical size={'1rem'} class="min-w-4" style="color: var(--ds-text-mute)" />
								</div>
							</div>
						</td>
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
						<td>
							<div class="flex items-center gap-3">
								<div class="flex flex-wrap gap-2">
									{#each config.data.tags as tag, i}
										<IdentifierLink
											identifier={tag}
											context="tag"
											globalState={data.globalState}
											solidBackground
										/>
									{/each}
								</div>
								<button
									class="p-0 shrink-0"
									style="color: var(--ds-text-mute)"
									onclick={() => (currentlyEditingConfig = config.data)}
								>
									<Pen size={'0.875rem'} class="min-w-4" />
								</button>
							</div>
						</td>
						<td>
							<RowActions>
								<ActionButton
									label={$t('configurations.actions.view-details')}
									icon={Search}
									href={`/configuration/configuration-details?${buildGlobalNavSearchParam(
										data.globalState,
										$page.url.search,
										'config',
										config.data.identifier
									)}`}
								/>
								<ActionButton
									label={$t('nav.configure')}
									icon={Sliders}
									href={`/configuration/edit?${buildGlobalNavSearchParam(
										data.globalState,
										$page.url.search,
										'config',
										config.data.identifier
									)}`}
								/>
								<ActionButton
									label={$t('configurations.actions.delete')}
									icon={Trash}
									variant="danger"
									onclick={() => (configToDelete = config.data)}
								/>
							</RowActions>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</Page>
