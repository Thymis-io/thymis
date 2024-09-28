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

	let className = '';
	export { className as class };
</script>

<Section class={className} title={$t('device-details.actions')}>
	<Button
		class="px-4 py-2 gap-2"
		color="alternative"
		on:click={() => buildAndDownloadImage(device)}
	>
		<Download size="20" />
		{$t('devices.actions.download')}
	</Button>
	<div />
	<Button class="px-4 py-2 gap-2" color="alternative" on:click={() => restartDevice(device)}>
		<RotateCcw size="20" />
		{$t('devices.actions.restart')}
	</Button>
	<div />
</Section>
