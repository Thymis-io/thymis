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
		TableHeadCell
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
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';

	const flipDurationMs = 200;
	let dragDisabled = true;

	let deviceToDelete: Device | undefined = undefined;

	export let data: PageData;

	const deleteDevice = async (device: Device) => {
		data.state.devices = data.state.devices.filter((d) => d.identifier !== device.identifier);
		await saveState();
	};

	const restartDevice = async (device: Device) => {
		fetch(`/api/action/restart-device?identifier=${device.identifier}`, { method: 'POST' });
	};

	const buildAndDownloadImage = async (device: Device) => {
		console.log('Building and downloading image');
		await fetch(`/api/action/build-download-image?identifier=${device.identifier}`, {
			method: 'POST'
		});
	};

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
		return { id: d.identifier, data: d };
	});

	let deviceModalOpen = false;
	let currentlyEditingDevice: Device | undefined = undefined;
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4 flex-col items-start xl:flex-row xl:items-center">
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
	</div>
	<DeployActions />
</div>
<CreateDeviceModal bind:open={deviceModalOpen} />
<DeleteConfirm
	target={deviceToDelete?.displayName}
	on:confirm={() => {
		if (deviceToDelete) deleteDevice(deviceToDelete);
		deviceToDelete = undefined;
	}}
	on:cancel={() => (deviceToDelete = undefined)}
/>
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
				<TableBodyEditCell bind:value={device.data.targetHost} onEnter={() => saveState()} />
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex justify-between">
						<div class="flex gap-2">
							{#each device.data.tags as tag, i}
								<Button
									pill
									size="sm"
									class="p-3 py-1.5"
									href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
								>
									<TagIcon size={20} class="mr-2" />
									<!-- <span
									class="inline-block bg-blue-300 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-1"
								> -->
									{findTag(tag)?.displayName ?? tag}
									<!-- </span> -->
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
							href={`/config?${buildGlobalNavSearchParam(
								$page.url.search,
								'device',
								device.data.identifier
							)}`}
						>
							{$t('devices.actions.edit')}
						</Button>
						<Button
							class="px-4 py-2"
							color="alternative"
							on:click={() => buildAndDownloadImage(device.data)}
						>
							{$t('devices.actions.download')}
						</Button>
						<Button
							class="px-4 py-2"
							color="alternative"
							on:click={() => restartDevice(device.data)}
						>
							{$t('devices.actions.restart')}
						</Button>
						<Button
							class="ml-8 px-4 py-2"
							color="alternative"
							on:click={() => (deviceToDelete = device.data)}
						>
							{$t('devices.actions.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
