<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Device, type Tag } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import {
		Button,
		Helper,
		Table,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Tooltip
	} from 'flowbite-svelte';
	import TagIcon from 'lucide-svelte/icons/tag';
	import Plus from 'lucide-svelte/icons/plus';
	import Search from 'lucide-svelte/icons/search';
	import GripVertical from 'lucide-svelte/icons/grip-vertical';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import CreateDeviceModal from './CreateDeviceModal.svelte';
	import EditTagModal from './EditTagModal.svelte';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { PageData } from './$types';
	import { dndzone, SOURCES, TRIGGERS, type DndEvent } from 'svelte-dnd-action';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import type { KeyboardEventHandler, MouseEventHandler, TouchEventHandler } from 'svelte/elements';
	import { flip } from 'svelte/animate';
	import { nameToIdentifier, nameValidation } from '$lib/nameValidation';
	import { fetchWithNotify } from '$lib/fetchWithNotify';

	const flipDurationMs = 200;
	let dragDisabled = true;

	export let data: PageData;

	const findTag = (identifier: string) => {
		return data.state.tags.find((t) => t.identifier === identifier);
	};

	const handleConsider = (e: CustomEvent<DndEvent<{ id: string; data: Device }>>) => {
		const {
			items: newItems,
			info: { source, trigger }
		} = e.detail;
		devices = newItems;
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
	};
	const handleFinalize = (e: CustomEvent<DndEvent<{ id: string; data: Device }>>) => {
		const {
			items: newItems,
			info: { source }
		} = e.detail;
		devices = newItems;
		// also send new device order to backend and reload
		let devicesState = devices.map((d) => d.data);
		data.state.devices = devicesState;
		saveState();
		// Ensure dragging is stopped on drag finish via pointer (mouse, touch)
		if (source === SOURCES.POINTER) {
			dragDisabled = true;
		}
	};
	const startDrag = ((e) => {
		// preventing default to prevent lag on touch devices (because of the browser checking for screen scrolling)
		e.preventDefault();
		dragDisabled = false;
	}) satisfies TouchEventHandler<HTMLDivElement> & MouseEventHandler<HTMLDivElement>;
	const handleKeyDown = ((e) => {
		if ((e.key === 'Enter' || e.key === ' ') && dragDisabled) dragDisabled = false;
	}) satisfies KeyboardEventHandler<HTMLDivElement>;

	const renameDevice = async (device: Device, displayName: string) => {
		const oldIdentifier = device.identifier;
		const identifier = nameToIdentifier(displayName);

		if (identifier && !data.state.devices.some((d) => d.identifier === identifier)) {
			device.displayName = displayName;
			device.identifier = identifier;

			const success = await saveState();

			if (success) {
				const oldHostkeyRequest = await fetchWithNotify(
					`/api/hostkey/${oldIdentifier}`,
					undefined,
					{ 404: null }
				);

				if (oldHostkeyRequest.ok) {
					const oldHostkey = await oldHostkeyRequest.json();
					await fetchWithNotify(`/api/hostkey/${identifier}`, {
						method: 'PUT',
						headers: {
							'Content-Type': 'application/json'
						},
						body: JSON.stringify(oldHostkey)
					});
					await fetchWithNotify(`/api/hostkey/${oldIdentifier}`, { method: 'DELETE' });
				}
				return true;
			}
		}

		return false;
	};

	$: devices = data.state.devices.map((d) => {
		return { id: d.identifier, data: d };
	});

	let deviceModalOpen = false;
	let currentlyEditingDevice: Device | undefined = undefined;
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4">
		<h1 class="text-3xl font-bold dark:text-white">{$t('nav.devices')}</h1>
		<Button
			color="alternative"
			class="whitespace-nowrap gap-2 px-2 py-1 m-1"
			on:click={() => (deviceModalOpen = true)}
			disabled={devices.length >= 5}
		>
			<Plus size={20} />
			{$t('devices.create-new', {
				values: {
					deviceCount: devices.length,
					deviceLimit: 5
				}
			})}
		</Button>
	</div>
	{#if devices.length >= 5}
		<Tooltip class="z-50 whitespace-pre">
			{$t('devices.limit-explain', {
				values: {
					deviceLimit: 5
				}
			})}
		</Tooltip>
	{/if}
	<DeployActions />
</div>
<CreateDeviceModal bind:open={deviceModalOpen} />
<EditTagModal bind:currentlyEditingDevice />
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('devices.table.name')}</TableHeadCell>
		<!-- <TableHeadCell padding="p-2">{$t('devices.table.target-host')}</TableHeadCell> -->
		<TableHeadCell padding="p-2">{$t('devices.table.tags')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('devices.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody
		use:dndzone={{ items: devices, dragDisabled, flipDurationMs }}
		on:consider={handleConsider}
		on:finalize={handleFinalize}
	>
		{#each devices as device (device.id)}
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
							on:mousedown={startDrag}
							on:touchstart={startDrag}
							on:keydown={handleKeyDown}
						>
							<GripVertical size={'1rem'} class="min-w-4" />
						</div>
					</div>
				</TableBodyCell>
				<TableBodyEditCell
					value={device.data.displayName}
					onEnter={async (value) => {
						const success = await renameDevice(device.data, value);

						if (!success) {
							// Reset the display name if the rename was unsuccessful
							device.data.displayName = device.data.displayName;
						}
					}}
				>
					<svelte:fragment slot="bottom" let:value={newDisplayName}>
						{#if nameValidation(newDisplayName, 'device')}
							{#if newDisplayName !== device.data.displayName}
								<Helper color="red">{nameValidation(newDisplayName, 'device')}</Helper>
							{/if}
						{:else}
							<Helper color="green">
								{$t('create-device.name-helper', {
									values: { identifier: nameToIdentifier(newDisplayName) }
								})}
							</Helper>
						{/if}
					</svelte:fragment>
				</TableBodyEditCell>
				<!-- <TableBodyCell>{$t('devices.unknown-target')}</TableBodyCell> -->
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex justify-between">
						<div class="flex gap-2">
							{#each device.data.tags as tag, i}
								<Button
									size="sm"
									class="p-2 py-0.5 gap-1"
									href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
								>
									<TagIcon size={'0.75rem'} class="min-w-3" />
									<span class="text-nowrap">
										{findTag(tag)?.displayName ?? tag}
									</span>
								</Button>
							{/each}
						</div>
						<button class="btn ml-2 p-0" on:click={() => (currentlyEditingDevice = device.data)}>
							<Pen size={'1rem'} class="min-w-4" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-1 px-2 md:px-4">
					<div class="flex gap-2">
						<Button
							class="px-3 py-1.5 gap-2"
							color="alternative"
							href={`/device-details?${buildGlobalNavSearchParam(
								$page.url.search,
								'device',
								device.data.identifier
							)}`}
						>
							<Search size={18} class="min-w-3" />
							{$t('devices.actions.view-details')}
						</Button>
					</div>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
