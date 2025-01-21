<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { saveState, type Device, state } from '$lib/state';
	import { Button } from 'flowbite-svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import Trash from 'lucide-svelte/icons/trash-2';
	import { goto } from '$app/navigation';

	export let device: Device;

	let deviceToDelete: Device | undefined = undefined;

	const deleteDevice = async (device: Device) => {
		$state.devices = $state.devices.filter((d) => d.identifier !== device.identifier);
		await saveState();
		await goto('/configuration/list');
	};

	let className = '';
	export { className as class };
</script>

<DeleteConfirm
	target={deviceToDelete?.displayName}
	on:confirm={() => {
		if (deviceToDelete) deleteDevice(deviceToDelete);
		deviceToDelete = undefined;
	}}
	on:cancel={() => (deviceToDelete = undefined)}
/>
<Section class={className} title={$t('configuration-details.danger')}>
	<Button
		class="px-2 py-1.5 gap-2 justify-start"
		color="alternative"
		on:click={() => (deviceToDelete = device)}
	>
		<Trash size="16" />
		{$t('configurations.actions.delete')}
	</Button>
</Section>
