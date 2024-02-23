<script lang="ts">
	import { getModalStore } from '@skeletonlabs/skeleton';
	import { saveState, type Device, state } from '$lib/state';
	import Pen from 'lucide-svelte/icons/pen';
	import { controllerHost, controllerProtocol } from '$lib/api';

	const modalStore = getModalStore();

	function openCreateDeviceModal() {
		modalStore.trigger({
			type: 'component',
			component: 'CreateDeviceModal',
			title: 'Create a new device',
			response: (r) => {
				if (r && $state) {
					$state.devices = [...$state.devices, { ...r, tags: [], modules: [] }];
					saveState($state);
				}
			}
		});
	}

	function openEditTagModal(device: Device | undefined) {
		if (!device) return;

		modalStore.trigger({
			type: 'component',
			component: 'EditTagModal',
			title: 'Edit tags',
			meta: { tags: device.tags, availableTags: $state?.tags },
			response: (r) => {
				if (r && $state) {
					$state.tags = r.availableTags;
					$state.devices = $state.devices.map((d) => {
						if (d.hostname === device.hostname) d.tags = r.deviceTags;
						return d;
					});
					saveState($state);
				}
			}
		});
	}

	function deleteDevice(device: Device) {
		if ($state) {
			$state.devices = $state.devices.filter((d) => d.hostname !== device.hostname);
			saveState($state);
		}
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

	const openEditHostnameModal = (device: Device) => {
		modalStore.trigger({
			type: 'component',
			component: 'EditHostnameModal',
			title: 'Edit hostname',
			meta: { hostname: device.hostname },
			response: (r) => {
				if (r && $state) {
					$state.devices = $state.devices.map((d) => {
						if (d.hostname === device.hostname) d.hostname = r.hostname;
						return d;
					});
					saveState($state);
				}
			}
		});
	};
</script>

<button class="btn variant-filled mb-8" on:click={() => openCreateDeviceModal()}>
	Create New Device
</button>
<div class="card">
	<header class="card-header" />
	<section class="p-4">
		<table class="table-auto w-full text-left">
			<thead>
				<tr class="">
					<th class="border-b border-slate-100 p-2">Name</th>
					<th class="border-b border-slate-100 p-2">Hostname</th>
					<th class="border-b border-slate-100 p-2">Tags</th>
					<th class="border-b border-slate-100 p-2">Actions</th>
					<th class="border-b border-slate-100 p-2">Status</th>
				</tr>
			</thead>
			<tbody>
				{#each $state?.devices ?? [] as device}
					<tr>
						<td class="border-t border-slate-200 p-2">{device.displayName}</td>
						<td class="border-t border-slate-200 p-2">
							{device.hostname}
							<button class="btn ml-2 p-0" on:click={() => openEditHostnameModal(device)}>
								<Pen size="20" />
							</button>
						</td>
						<td class="border-t border-slate-200 p-2 flex gap-1 group">
							{#each device.tags as tag, i}
								<!-- <span> -->
								<!-- <a class="underline" href="/config?tag={tag}">{tag}</a
									>{#if i < device.tags.length - 1}{', '}{/if} -->
								<a href="/config?tag={tag}">
									<!-- style like badge -->
									<span
										class="inline-block bg-blue-300 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-1"
									>
										{tag}
									</span>
								</a>
								<!-- </span> -->
							{/each}
							<div class="w-8">
								<button class="btn ml-2 p-0" on:click={() => openEditTagModal(device)}>
									<Pen size="20" />
								</button>
							</div>
						</td>
						<td class="border-t border-slate-200 p-2">
							<a class="btn variant-filled" href="/config?device={device.hostname}">Edit</a>
							<!-- <a href="." class="btn variant-filled">Download Image</a> -->
							<button class="btn variant-filled" on:click={() => buildAndDownloadImage(device)}>
								Download Image
							</button>
							<button class="btn variant-filled" on:click={() => deleteDevice(device)}>
								Delete
							</button>
						</td>
						<td class="border-t border-slate-200 p-2">Online</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</section>
</div>
