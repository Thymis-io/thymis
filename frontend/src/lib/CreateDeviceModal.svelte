<script lang="ts">
	import InstallationStepper from '$lib/InstallationStepper.svelte';
	import { Modal } from 'flowbite-svelte';
	import type { PageData } from '../routes/$types';
	import { saveState, type Device, type State } from './state';

	export let state: State;
	export let open = false;
	export let onClose: (() => void) | undefined = undefined;

	function onSubmit(submitData: Device): void {
		state.devices = [...state.devices, { ...submitData }];
		saveState(state);
	}
</script>

<Modal title="Create a new device" bind:open outsideclose size={'lg'} on:close={() => onClose?.()}>
	<InstallationStepper {onSubmit} />
</Modal>
