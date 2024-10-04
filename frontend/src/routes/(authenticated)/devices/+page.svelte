<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Device, type Tag } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import {
		Button,
		Table,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Tooltip
	} from 'flowbite-svelte';
	import TagIcon from 'lucide-svelte/icons/tag';
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
	import { nameToIdentifier } from '$lib/nameValidation';

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

	$: devices = data.state.devices.map((d) => {
		console.log(data.registeredDevices);
		return { id: d.identifier, data: d };
	});

	let deviceModalOpen = false;
	let currentlyEditingDevice: Device | undefined = undefined;
</script>

<div class="flex justify-between mb-4">
	<Button
		color="alternative"
		class="whitespace-nowrap"
		on:click={() => (deviceModalOpen = true)}
		disabled={devices.length >= 5}
	>
		{$t('devices.create-new', {
			values: {
				deviceCount: devices.length,
				deviceLimit: 5
			}
		})}
	</Button>
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
	<TableHead>
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('devices.table.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('devices.table.target-host')}</TableHeadCell>
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
				class="border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
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
							<GripVertical size="20" />
						</div>
					</div>
				</TableBodyCell>
				<TableBodyEditCell
					bind:value={device.data.displayName}
					onEnter={() => {
						device.data.identifier = nameToIdentifier(device.data.displayName);
						saveState();
					}}
				/>
				<TableBodyCell>{$t('devices.unknown-target')}</TableBodyCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex justify-between">
						<div class="flex gap-2">
							{#each device.data.tags as tag, i}
								<Button
									pill
									size="sm"
									class="p-2 py-0.5"
									href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
								>
									<TagIcon size={15} class="mr-1" />
									<span class="text-nowrap">
										{findTag(tag)?.displayName ?? tag}
									</span>
								</Button>
							{/each}
						</div>
						<button class="btn ml-2 p-0" on:click={() => (currentlyEditingDevice = device.data)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex gap-2">
						<Button
							class="px-4 py-2"
							color="alternative"
							href={`/device-details?${buildGlobalNavSearchParam(
								$page.url.search,
								'device',
								device.data.identifier
							)}`}
						>
							{$t('devices.actions.view-details')}
						</Button>
					</div>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
