<script lang="ts">
	import { t } from 'svelte-i18n';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/PageHead.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import { browser } from '$app/environment';

	export let data: PageData;

	let columns = data.vncDisplaysPerColumn;
</script>

<PageHead title={$t('nav.global-vnc')} repoStatus={data.repoStatus} />
<div class="flex items-center mb-2">
	{$t('vnc.column-count')}
	<Dropdown
		values={[1, 2, 3, 4, 5, 6]}
		showBox={false}
		selected={columns}
		onSelected={(value) => {
			columns = value;
			if (browser) document.cookie = `vnc-displays-per-column=${columns}; SameSite=Lax;`;
		}}
		class="min-w-10"
	/>
</div>
<DynamicGrid class={columns === 2 ? 'gap-4' : 'gap-2'} {columns}>
	{#each data.allDeploymentInfos as deploymentInfo}
		{@const config = data.state.configs.find(
			(d) => d.identifier === deploymentInfo.deployed_config_id
		)}
		{#if config && targetShouldShowVNC(config, $state)}
			<div>
				<p class=" mb-2 text-center text-gray-900 dark:text-white">{config.displayName}</p>
				<VncView {config} {deploymentInfo} />
			</div>
		{/if}
	{/each}
</DynamicGrid>
