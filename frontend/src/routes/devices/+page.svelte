<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { saveState, type Device, type Tag } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import {
		Button,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import TagIcon from 'lucide-svelte/icons/tag';
	import GripVertical from 'lucide-svelte/icons/grip-vertical';
	import { controllerHost, controllerProtocol } from '$lib/api';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import CreateDeviceModal from './CreateDeviceModal.svelte';
	import EditTagModal from './EditTagModal.svelte';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { PageData } from './$types';
	import { dndzone, SOURCES, TRIGGERS } from 'svelte-dnd-action';
	import { flip } from 'svelte/animate';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';

	const flipDurationMs = 200;
	let dragDisabled = true;

	export let data: PageData;

	function deleteDevice(device: Device) {
		data.state.devices = data.state.devices.filter((d) => d.identifier !== device.identifier);
		saveState(data.state);
	}

	const downloadUri = (uri: string) => {
		const link = document.createElement('a');
		link.href = uri;
		link.download = 'image.img';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	};

	const buildAndDownloadImage = async (device: Device) => {
		console.log('Building and downloading image');
		await fetch(
			`${controllerProtocol}://${controllerHost}/action/build-download-image?identifier=${device.identifier}`,
			{
				method: 'POST'
			}
		);
	};

	const findTag = (identifier: string) => {
		return data.state.tags.find((t) => t.identifier === identifier);
	};

	enum ModalType {
		None,
		CreateDevice,
		EditTags
	}

	let openModal = ModalType.None;
	let editDevice: Device | undefined;

	const openCreateDeviceModal = () => {
		openModal = ModalType.CreateDevice;
	};

	const closeCreateDeviceModal = () => {
		openModal = ModalType.None;
	};

	const openEditTagModal = (device: Device) => {
		openModal = ModalType.None;
		openModal = ModalType.EditTags;
		editDevice = device;
	};

	const closeEditTagModal = () => {
		openModal = ModalType.None;
		editDevice = undefined;
	};

	const saveEditTagModal = (tags: string[], availableTags: Tag[]) => {
		if (editDevice) {
			editDevice.tags = tags;
			data.state.tags = availableTags;
			saveState(data.state);
		}
	};

	function handleConsider(e) {
		const {
			items: newItems,
			info: { source, trigger }
		} = e.detail;
		devices = newItems;
		// Ensure dragging is stopped on drag finish via keyboard
		if (source === SOURCES.KEYBOARD && trigger === TRIGGERS.DRAG_STOPPED) {
			dragDisabled = true;
		}
		console.log('consider', newItems);
	}
	function handleFinalize(e) {
		const {
			items: newItems,
			info: { source }
		} = e.detail;
		devices = newItems;
		// also send new device order to backend and reload
		let devicesState = devices.map((d) => d.data);
		data.state.devices = devicesState;
		saveState(data.state);
		// Ensure dragging is stopped on drag finish via pointer (mouse, touch)
		if (source === SOURCES.POINTER) {
			dragDisabled = true;
		}
		console.log('finalize', newItems);
	}
	function startDrag(e) {
		// preventing default to prevent lag on touch devices (because of the browser checking for screen scrolling)
		e.preventDefault();
		dragDisabled = false;
	}
	function handleKeyDown(e) {
		if ((e.key === 'Enter' || e.key === ' ') && dragDisabled) dragDisabled = false;
	}

	$: devices = data.state.devices.map((d) => {
		return { id: d.identifier, data: d };
	});
</script>

<div class="flex justify-between mb-4">
	<Button color="alternative" on:click={() => openCreateDeviceModal()}>
		{$t('devices.create-new')}
	</Button>
	<DeployActions />
</div>
<CreateDeviceModal
	open={openModal === ModalType.CreateDevice}
	onClose={closeCreateDeviceModal}
	thymisDevice={data.availableModules.find(
		(m) => m.type === 'thymis_controller.models.modules.thymis.ThymisDevice'
	)}
/>
<EditTagModal
	tags={editDevice?.tags ?? []}
	availableTags={data.state.tags}
	open={openModal === ModalType.EditTags}
	onClose={closeEditTagModal}
	onSave={saveEditTagModal}
/>
<Table shadow>
	<TableHead>
		<TableHeadCell />
		<TableHeadCell>{$t('devices.table.name')}</TableHeadCell>
		<TableHeadCell>{$t('devices.table.target-host')}</TableHeadCell>
		<TableHeadCell>{$t('devices.table.tags')}</TableHeadCell>
		<TableHeadCell>{$t('devices.table.actions')}</TableHeadCell>
		<TableHeadCell>{$t('devices.table.status')}</TableHeadCell>
	</TableHead>
	<tbody
		use:dndzone={{ items: devices, dragDisabled, flipDurationMs }}
		on:consider={handleConsider}
		on:finalize={handleFinalize}
	>
		{#each devices as device (device.id)}
			<TableBodyRow>
				<TableBodyCell>
					<div class="flex gap-1">
						<div
							tabindex={dragDisabled ? 0 : -1}
							aria-label="drag-handle"
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
					onEnter={() => saveState(data.state)}
				/>
				<TableBodyEditCell
					bind:value={device.data.targetHost}
					onEnter={() => saveState(data.state)}
				/>
				<TableBodyCell>
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
						<button class="btn ml-2 p-0" on:click={() => openEditTagModal(device.data)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					<div class="flex gap-2">
						<Button
							color="alternative"
							href={`/config?${buildGlobalNavSearchParam(
								$page.url.search,
								'device',
								device.data.identifier
							)}`}
						>
							{$t('devices.actions.edit')}
						</Button>
						<Button color="alternative" on:click={() => buildAndDownloadImage(device.data)}>
							{$t('devices.actions.download')}
						</Button>
						<Button color="alternative" on:click={() => deleteDevice(device.data)}>
							{$t('devices.actions.delete')}
						</Button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					{$t('devices.status.online')}
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</tbody>
</Table>
