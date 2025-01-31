<script lang="ts">
	import { t } from 'svelte-i18n';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/PageHead.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';

	export let data: PageData;

	$: columnsParam = queryParam('vnc-columns');
	$: columns = parseInt($columnsParam ?? '3');
</script>

<PageHead title={$t('nav.global-vnc')} />
<div class="flex items-center mb-2">
	{$t('vnc.column-count')}
	<Dropdown
		values={[1, 2, 3, 4, 5, 6]}
		showBox={false}
		selected={columns}
		onSelected={(value) => ($columnsParam = value.toString())}
		class="min-w-10"
	/>
</div>
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
