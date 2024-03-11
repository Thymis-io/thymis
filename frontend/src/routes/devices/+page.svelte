<script lang="ts">
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
	import { controllerHost, controllerProtocol } from '$lib/api';
	import DeployActions from '$lib/DeployActions.svelte';
	import CreateDeviceModal from '$lib/CreateDeviceModal.svelte';
	import EditStringModal from '$lib/EditStringModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import type { PageData } from './$types';

	export let data: PageData;

	function deleteDevice(device: Device) {
		data.state.devices = data.state.devices.filter((d) => d.hostname !== device.hostname);
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

	const buildAndDownloadImage = (device: Device) => {
		console.log('Building and downloading image');
		downloadUri(
			`${controllerProtocol}://${controllerHost}/action/build-download-image?hostname=${device.hostname}`
		);
	};

	enum ModalType {
		None,
		CreateDevice,
		EditName,
		EditHostname,
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

	const openEditNameModal = (device: Device) => {
		openModal = ModalType.EditName;
		editDevice = device;
	};

	const closeEditNameModal = () => {
		openModal = ModalType.None;
		editDevice = undefined;
	};

	const saveEditNameModal = (value: string) => {
		if (editDevice) {
			editDevice.displayName = value;
			saveState(data.state);
		}
	};

	const openEditHostnameModal = (device: Device) => {
		openModal = ModalType.EditHostname;
		editDevice = device;
	};

	const closeEditHostnameModal = () => {
		openModal = ModalType.None;
		editDevice = undefined;
	};

	const saveEditHostnameModal = (value: string) => {
		if (editDevice) {
			editDevice.hostname = value;
			saveState(data.state);
		}
	};

	const openEditTagModal = (device: Device) => {
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
</script>

<div class="flex justify-between mb-4">
	<Button color="alternative" on:click={() => openCreateDeviceModal()}>Create New Device</Button>
	<DeployActions />
</div>
<CreateDeviceModal
	{data}
	open={openModal === ModalType.CreateDevice}
	onClose={closeCreateDeviceModal}
/>
<EditStringModal
	title={'Edit Name'}
	value={editDevice?.displayName}
	open={openModal === ModalType.EditName}
	onClose={closeEditNameModal}
	onSave={saveEditNameModal}
/>
<EditStringModal
	title={'Edit Hostname'}
	value={editDevice?.hostname}
	open={openModal === ModalType.EditHostname}
	onClose={closeEditHostnameModal}
	onSave={saveEditHostnameModal}
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
		<TableHeadCell>Name</TableHeadCell>
		<TableHeadCell>Hostname</TableHeadCell>
		<TableHeadCell>Tags</TableHeadCell>
		<TableHeadCell>Actions</TableHeadCell>
		<TableHeadCell>Status</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each data.state.devices as device}
			<TableBodyRow>
				<TableBodyCell>
					<div class="flex gap-1">
						{device.displayName}
						<button class="btn ml-2 p-0" on:click={() => openEditNameModal(device)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					<div class="flex gap-1">
						{device.hostname}
						<button class="btn ml-2 p-0" on:click={() => openEditHostnameModal(device)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					<div class="flex gap-1">
						{#each device.tags as tag, i}
							<Button pill size="sm" class="p-3 py-1.5" href="/config?tag={tag}">
								<TagIcon size={20} class="mr-2" />
								<!-- <span
									class="inline-block bg-blue-300 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-1"
								> -->
								{tag}
								<!-- </span> -->
							</Button>
						{/each}
						<button class="btn ml-2 p-0" on:click={() => openEditTagModal(device)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					<div class="flex gap-2">
						<Button color="alternative" href="/config?device={device.hostname}">Edit</Button>
						<Button color="alternative" on:click={() => buildAndDownloadImage(device)}>
							Download Image
						</Button>
						<Button color="alternative" on:click={() => deleteDevice(device)}>Delete</Button>
					</div>
				</TableBodyCell>
				<TableBodyCell>Online</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
