<script lang="ts">
	import InstallationStepper from '$lib/InstallationStepper.svelte';
	import { Modal } from 'flowbite-svelte';
	import type { PageData } from '../routes/$types';
	import { saveState } from './state';

	export let data: PageData;
	export let openModal = false;

	function onSubmit(submitData: any): void {
		data.state.devices = [...data.state.devices, { ...submitData, tags: [], modules: [] }];
		saveState(data.state);
	}
</script>

<Modal title="Create a new device" bind:open={openModal} outsideclose size={'lg'}>
	<InstallationStepper {onSubmit} />
</Modal>
