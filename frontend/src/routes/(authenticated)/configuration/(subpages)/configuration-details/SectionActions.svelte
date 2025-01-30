<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Device } from '$lib/state';
	import { Button, Input, Tooltip } from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import Play from 'lucide-svelte/icons/play';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { getConfigImageFormat } from '$lib/config/configUtils';

	export let device: Device;

	const restartDevice = async (device: Device) => {
		await fetchWithNotify(`/api/action/restart-device?identifier=${device.identifier}`, {
			method: 'POST'
		});
	};

	const buildAndDownloadImage = async (device: Device) => {
		await fetchWithNotify(`/api/action/build-download-image?identifier=${device.identifier}`, {
			method: 'POST'
		});
	};

	let className = '';
	export { className as class };

	$: image_format = getConfigImageFormat(device);
</script>

<Section class={className} title={$t('configuration-details.actions')}>
	<Button
		class="px-2 py-1.5 gap-2 flex justify-start"
		color="alternative"
		on:click={() => buildAndDownloadImage(device)}
	>
		{#if image_format == 'nixos-vm'}
			<Play size={'1rem'} class="min-w-4" />
			{$t('configurations.actions.build_vm_and_start')}
		{:else}
			<Download size={'1rem'} class="min-w-4" />
			{$t('configurations.actions.download')}
		{/if}
	</Button>
	<Button
		class="px-2 py-1.5 gap-2 justify-start"
		color="alternative"
		on:click={() => restartDevice(device)}
	>
		<RotateCcw size={'1rem'} class="min-w-4" />
		{$t('configurations.actions.restart')}
	</Button>
</Section>
