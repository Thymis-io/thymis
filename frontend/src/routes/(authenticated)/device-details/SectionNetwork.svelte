<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { saveState, type Device } from '$lib/state';
	import { Input } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import clickOutside from 'svelte-outside-click';

	export let device: Device;

	let editTargetHost: string | undefined = undefined;

	const setTargetHost = (value: string | undefined) => {
		if (value === undefined || value === device.targetHost) {
			editTargetHost = undefined;
			return;
		}

		device.targetHost = value;
		saveState();
		editTargetHost = undefined;
	};

	let className = '';
	export { className as class };
</script>

<Section class={className} title={$t('device-details.network')}>
	<p>{$t('device-details.targetHost')}:</p>
	<div class="flex" use:clickOutside={() => setTargetHost(editTargetHost)}>
		{#if !editTargetHost}
			<p class="min-w-32 h-[28px]">{device.targetHost}</p>
		{:else}
			<Input
				size="sm"
				class="w-32 h-[32px] mt-[-4px] "
				bind:value={editTargetHost}
				on:keydown={(e) => e.key === 'Enter' && setTargetHost(editTargetHost)}
			/>
		{/if}
		<button
			class="btn ml-4 p-0"
			on:click={() => {
				if (editTargetHost !== undefined) {
					setTargetHost(editTargetHost);
				} else {
					editTargetHost = device.targetHost;
				}
			}}
		>
			<Pen size="20" />
		</button>
	</div>
</Section>
