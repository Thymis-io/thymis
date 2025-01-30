<script lang="ts">
	import { t } from 'svelte-i18n';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/PageHead.svelte';
	import { queryParam } from 'sveltekit-search-params';

	export let data: PageData;

	const defaultColumns = '3';
	$: columns = queryParam('vnc-columns');

	const setColumns = (e: Event) => {
		$columns = (e.target as HTMLInputElement).value;
	};
</script>

<PageHead title={$t('nav.global-vnc')} />
<input
	type="range"
	min={1}
	max={6}
	step={1}
	value={parseInt($columns ?? defaultColumns)}
	on:change={(e) => setColumns(e)}
	class="range my-4 w-full"
/>
<div
	class="grid"
	style={`grid-template-columns: repeat(${$columns ?? defaultColumns}, minmax(0, 1fr)); gap: ${$columns === '2' ? '1em' : '0.5em'};`}
>
	{#each data.allDeploymentInfos as [configId, deploymentInfos]}
		{@const device = data.state.devices.find((d) => d.identifier === configId)}
		{#if device && targetShouldShowVNC(device, $state)}
			{#each deploymentInfos as deploymentInfo}
				<div>
					<p class=" mb-2 text-center text-gray-900 dark:text-white">{device.displayName}</p>
					<VncView {device} {deploymentInfo} />
				</div>
			{/each}
		{/if}
	{/each}
</div>

<style>
	.range {
		background: transparent !important;
	}
</style>
