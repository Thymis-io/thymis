<script lang="ts">
	import InstallationStepper from '$lib/InstallationStepper.svelte';
	import { Modal } from 'flowbite-svelte';
	import type { PageData } from '../routes/$types';
	import { saveState } from './state';

	export let data: PageData;
	export let open = false;
	export let onClose: (() => void) | undefined = undefined;

	function onSubmit(submitData: any): void {
		data.state.devices = [...data.state.devices, { ...submitData, tags: [], modules: [] }];
		saveState(data.state);
	}
</script>

<Modal title="Create a new device" bind:open outsideclose size={'lg'} on:close={() => onClose?.()}>
	<InstallationStepper {onSubmit} />
</Modal>
