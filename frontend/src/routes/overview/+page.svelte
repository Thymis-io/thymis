<script lang="ts">
	import type { PageData } from './$types';
	import { getModalStore } from '@skeletonlabs/skeleton';
	import { saveState, type Device } from '$lib/state';

	export let data: PageData;
	$: state = data.state;

	const modalStore = getModalStore();

	function openCreateDeviceModal() {
		modalStore.trigger({
			type: 'component',
			component: 'CreateDeviceModal',
			title: 'Create a new device',
			response: (r) => {
				if (r) {
					state.devices.push({ ...r, tags: [], modules: [] });
					saveState(state);
				}
			}
		});
	}

	function deleteDevice(device: Device) {
		state.devices = state.devices.filter(
			(d) => d.hostname !== device.hostname && d.displayName !== device.displayName
		);
		saveState(state);
	}
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
				{#each state.devices as device}
					<tr>
						<td class="border-t border-slate-200 p-2">{device.displayName}</td>
						<td class="border-t border-slate-200 p-2">{device.hostname}</td>
						<td class="border-t border-slate-200 p-2">
							{#each device.tags as tag, i}
								<a class="underline" href="/config?tag={tag}">{tag}</a
								>{#if i < device.tags.length - 1}{', '}{/if}
							{/each}
						</td>
						<td class="border-t border-slate-200 p-2">
							<a class="btn variant-filled" href="/config?device={device.hostname}">Edit</a>
							<a class="btn variant-filled">Download Image</a>
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
