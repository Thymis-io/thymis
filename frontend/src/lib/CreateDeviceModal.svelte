<script lang="ts">
	import { t } from 'svelte-i18n';
	import InstallationStepper from '$lib/InstallationStepper.svelte';
	import { Modal } from 'flowbite-svelte';
	import { saveState, type Device, type State, type ModuleDefinition } from './state';

	export let state: State;
	export let open = false;
	export let onClose: (() => void) | undefined = undefined;
	export let thymisDevice: ModuleDefinition | undefined = undefined;

	function onSubmit(submitData: Device): void {
		state.devices = [...state.devices, { ...submitData }];
		saveState(state);
	}
</script>

<Modal
	title={$t('create-device.title')}
	bind:open
	outsideclose
	size={'lg'}
	on:close={() => onClose?.()}
>
	<InstallationStepper {onSubmit} {thymisDevice} />
</Modal>
