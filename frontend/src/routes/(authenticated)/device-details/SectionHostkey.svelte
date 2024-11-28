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

	let editHostKeyModalOpen = false;
</script>

<EditHostkeyModal bind:hostkey bind:open={editHostKeyModalOpen} {device} />
<Section class={className} title={$t('device-details.hostkey')}>
	<div class="flex flex-col gap-2">
		{#if hostkey}
			<div class="grid grid-cols-[max-content_1fr] gap-x-2">
				<p class="break-all text-base">{$t('device-details.targetHost')}:</p>
				<p class="break-all text-base">{hostkey.deviceHost}</p>
				<p class="break-all text-base">{$t('device-details.publicKey')}:</p>
				<p class="break-all text-base">{hostkey.publicKey}</p>
			</div>
		{/if}
		<div class="flex flex-row gap-2">
			{#if hostkey}
				<Button
					size="sm"
					class="gap-2 p-2 py-1.5"
					color="alternative"
					on:click={() => (editHostKeyModalOpen = true)}
				>
					<Pencil size={16} />
					<span class="text.-base">{$t('device-details.edit-hostkey')}</span>
				</Button>
			{:else}
				<Button
					size="sm"
					class="gap-2"
					color="alternative"
					on:click={() => (editHostKeyModalOpen = true)}
				>
					<PlusCircle size={'1rem'} class="min-w-4" />
					<span>{$t('device-details.add-hostkey')}</span>
				</Button>
			{/if}
		</div>
	</div>
</Section>
