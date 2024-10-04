<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { Hostkey } from '$lib/hostkey';
	import { Button } from 'flowbite-svelte';
	import { Pencil } from 'lucide-svelte/icons';
	import { Trash2, RefreshCw, PlusCircle } from 'lucide-svelte/icons';
	import type { Device } from '$lib/state';
	import EditHostkeyModal from './EditHostkeyModal.svelte';

	export let hostkey: Hostkey | undefined;
	export let device: Device;
	console.log(device, 'AAAAAB');

	let className = '';
	export { className as class };

	const deleteHostkey = async () => {
		if (!hostkey) return;
		const response = await fetch(`/api/hostkey/${hostkey.identifier}`, {
			method: 'DELETE'
		});
		if (response.ok) {
			hostkey = undefined;
		} else {
			console.error('Unrecognized Error. Failed to delete hostkey');
		}
	};

	const refreshHostkey = async () => {
		if (!device) return;
		const response = await fetch(`/api/hostkey/${device.identifier}`, {
			method: 'GET'
		});
		if (response.ok) {
			hostkey = await response.json();
		} else if (response.status === 404) {
			console.error('Hostkey not found');
			hostkey = undefined;
		} else {
			console.error('Unrecognized Error. Failed to refresh hostkey');
		}
	};

	let editHostKeyModalOpen = false;
</script>

<EditHostkeyModal bind:hostkey bind:open={editHostKeyModalOpen} {device} />
<Section class={className} title={$t('device-details.hostkey')}>
	<div class="flex flex-col">
		<div class="flex flex-row">
			{#if hostkey}
				<Button pill size="sm" class="p-2 py-1" on:click={() => (editHostKeyModalOpen = true)}>
					<Pencil size={15} class="mr-1" />
				</Button>
			{:else}
				<Button pill size="sm" class="p-2 py-1" on:click={() => (editHostKeyModalOpen = true)}>
					<PlusCircle size={15} class="mr-1" />
				</Button>
			{/if}
			<Button pill size="sm" class="p-2 py-1" on:click={() => refreshHostkey()}>
				<RefreshCw size={15} class="mr-1" />
			</Button>
			{#if hostkey}
				<Button pill size="sm" class="p-2 py-1" on:click={() => deleteHostkey()}>
					<Trash2 size={15} class="mr-1" />
				</Button>
			{/if}
		</div>
		{#if hostkey}
			<div class="flex flex-col">
				<p>{$t('device-details.targetHost')}: {hostkey.deviceHost}</p>
				<p>{$t('device-details.publicKey')}: {hostkey.publicKey}</p>
			</div>
		{/if}
	</div>
</Section>
