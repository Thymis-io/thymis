<script lang="ts">
	import { t } from 'svelte-i18n';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/PageHead.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import Slider from '$lib/components/Slider.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';

	export let data: PageData;

	$: columnsParam = queryParam('vnc-columns');
	$: columns = parseInt($columnsParam ?? '3');
</script>

<PageHead title={$t('nav.global-vnc')} />
<Slider
	min={1}
	max={6}
	step={1}
	value={columns}
	onChange={(value) => ($columnsParam = value.toString())}
/>
<DynamicGrid class={columns === 2 ? 'gap-4' : 'gap-2'} {columns}>
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
</DynamicGrid>
