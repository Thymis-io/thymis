<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Device } from '$lib/state';
	import { Button, Input, Tooltip } from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';

	export let device: Device;

	const restartDevice = async (device: Device) => {
		fetch(`/api/action/restart-device?identifier=${device.identifier}`, { method: 'POST' });
	};

	const buildAndDownloadImage = async (device: Device) => {
		console.log('Building and downloading image');
		await fetch(`/api/action/build-download-image?identifier=${device.identifier}`, {
			method: 'POST'
		});
	};

	const buildAndDownloadImageForClone = async (device: Device) => {
		console.log('Building and downloading image');
		const response = await fetch(
			`/api/action/build-download-image-for-clone?identifier=${device.identifier}`,
			{
				method: 'POST'
			}
		);
		if (response.ok) {
			// TODO update state
		} else {
			console.error('Failed to build and download image for clone');
		}
	};

	let className = '';
	export { className as class };
</script>

<Section class={className} title={$t('device-details.actions')}>
	<Button
		class="px-2 py-1.5 gap-2 flex justify-start"
		color="alternative"
		on:click={() => buildAndDownloadImage(device)}
	>
		<Download size={'1rem'} class="min-w-4" />
		{$t('devices.actions.download')}
	</Button>
	<Tooltip class="whitespace-pre">{$t('devices.actions.download-image-tooltip')}</Tooltip>
	<Button
		class="px-2 py-1.5 gap-2 flex justify-start"
		color="alternative"
		on:click={() => buildAndDownloadImageForClone(device)}
	>
		<Download size={'1rem'} class="min-w-4" />
		{$t('devices.actions.download-image-for-clone')}
	</Button>
	<Tooltip class="whitespace-pre">{$t('devices.actions.download-image-for-clone-tooltip')}</Tooltip>
	<Button
		class="px-2 py-1.5 gap-2 justify-start"
		color="alternative"
		on:click={() => restartDevice(device)}
	>
		<RotateCcw size={'1rem'} class="min-w-4" />
		{$t('devices.actions.restart')}
	</Button>
	<Tooltip>{$t('devices.actions.restart-tooltip')}</Tooltip>
</Section>
