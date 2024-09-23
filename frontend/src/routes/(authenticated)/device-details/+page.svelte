<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Button, Badge } from 'flowbite-svelte';
	import {
		saveState,
		type Device,
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import { Circle, Pen } from 'lucide-svelte';
	import TagIcon from 'lucide-svelte/icons/tag';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import EditTagModal from '../devices/EditTagModal.svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';

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

	let currentlyEditingDevice: Device | undefined = undefined;
	let deviceToDelete: Device | undefined = undefined;
</script>

<EditTagModal bind:currentlyEditingDevice />
<DeleteConfirm
	target={deviceToDelete?.displayName}
	on:confirm={() => {
		if (deviceToDelete) deleteDevice(deviceToDelete);
		deviceToDelete = undefined;
	}}
	on:cancel={() => (deviceToDelete = undefined)}
/>
<div class="flex justify-between mb-4">
	<div />
	<DeployActions />
</div>
{#if $globalNavSelectedTargetType === 'device' && $globalNavSelectedDevice}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter((device) => device.identifier === $globalNavSelectedDevice.identifier) as device}
			<div class="flex flex-wrap align-start gap-2">
				<h1>{device.displayName}</h1>
				<div>
					<Badge large size="sm" class="p-2 py-0.5">
						<Circle size={15} class="mr-1" color="lightgreen" />
						<span class="text-nowrap"> Online </span>
					</Badge>
				</div>
			</div>
			<div>
				<div class="flex flex-wrap align-start gap-2">
					<p>Host</p>
					<p>{device.targetHost}</p>
				</div>
				<div>
					<div class="flex justify-between">
						<div class="flex gap-2">
							{#each device.tags as tag, i}
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
						<button class="btn ml-2 p-0" on:click={() => (currentlyEditingDevice = device)}>
							<Pen size="20" />
						</button>
					</div>
				</div>
				<div>
					<div class="flex gap-2">
						<p>Module bearbeiten</p>
						<Button
							class="px-4 py-2"
							color="alternative"
							href={`/config?${buildGlobalNavSearchParam($page.url.search, 'device', device.identifier)}`}
						>
							{$t('devices.actions.edit')}
						</Button>
					</div>
				</div>
			</div>

			<div class="flex flex-wrap align-start gap-2">
				<Button
					class="px-4 py-2"
					color="alternative"
					on:click={() => buildAndDownloadImage(device)}
				>
					{$t('devices.actions.download')}
				</Button>
				<Button class="px-4 py-2" color="alternative" on:click={() => restartDevice(device)}>
					{$t('devices.actions.restart')}
				</Button>
				<Button
					class="ml-8 px-4 py-2"
					color="alternative"
					on:click={() => (deviceToDelete = device)}
				>
					{$t('devices.actions.delete')}
				</Button>
			</div>
		{/each}
	</div>
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<p>Test</p>
		{/each}
	</div>
{/if}
