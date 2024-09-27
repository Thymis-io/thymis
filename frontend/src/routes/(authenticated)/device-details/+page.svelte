<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Button, Badge, P } from 'flowbite-svelte';
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

	$: currentDevice = $globalNavSelectedDevice;
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
{#if $globalNavSelectedTargetType === 'device' && currentDevice}
	<div class="flex justify-between mb-4">
		<div class="flex flex-wrap gap-2">
			<h1 class="text-3xl font-bold dark:text-white">{currentDevice.displayName}</h1>
			<Badge large size="sm" class="p-2 py-0.5 self-center">
				<Circle size={15} class="mr-1" color="lightgreen" />
				<span class="text-nowrap"> Online </span>
			</Badge>
		</div>
		<DeployActions />
	</div>

	<div class="grid grid-cols-2 gap-4">
		<div class="grid grid-cols-1 gap-4">
			<div class="flex flex-wrap align-start gap-2 self-start">
				<p>Host</p>
				<p>{currentDevice.targetHost}</p>
			</div>
			<div>
				<div class="flex justify-between">
					<div class="flex gap-2 flex-wrap">
						{#each currentDevice.tags as tag, i}
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
					<button class="btn ml-2 p-0" on:click={() => (currentlyEditingDevice = currentDevice)}>
						<Pen size="20" />
					</button>
				</div>
			</div>
			<div>
				<div class="flex gap-2">
					<p class="self-center">Module bearbeiten</p>
					<Button
						class="px-4 py-2"
						color="alternative"
						href={`/config?${buildGlobalNavSearchParam($page.url.search, 'device', currentDevice.identifier)}`}
					>
						{$t('devices.actions.edit')}
					</Button>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1">
			<div class="flex flex-wrap align-start gap-2 self-start">
				<p>Actions</p>
			</div>
			<div class="flex flex-wrap align-start gap-2 self-start">
				<Button
					class="px-4 py-2"
					color="alternative"
					on:click={() => buildAndDownloadImage(currentDevice)}
				>
					{$t('devices.actions.download')}
				</Button>
				<Button class="px-4 py-2" color="alternative" on:click={() => restartDevice(currentDevice)}>
					{$t('devices.actions.restart')}
				</Button>
				<Button
					class="ml-8 px-4 py-2"
					color="alternative"
					on:click={() => (deviceToDelete = currentDevice)}
				>
					{$t('devices.actions.delete')}
				</Button>
			</div>
		</div>
	</div>
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<p>Test</p>
		{/each}
	</div>
{/if}
