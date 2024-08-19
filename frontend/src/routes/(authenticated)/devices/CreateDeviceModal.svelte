<script lang="ts">
	import { t } from 'svelte-i18n';
	import InstallationStepper from './InstallationStepper.svelte';
	import { Modal } from 'flowbite-svelte';
	import { type Device, type Module, saveState, state } from '$lib/state';

	export let open = false;
	export let onClose: (() => void) | undefined = undefined;
	export let thymisDevice: Module | undefined = undefined;

	function onSubmit(submitData: Device): void {
		$state.devices = [...$state.devices, { ...submitData }];
		saveState();
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
