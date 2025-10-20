<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import { browser } from '$app/environment';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let columns = $state(data.vncDisplaysPerColumn);
</script>

<PageHead
	title={$t('nav.global-vnc')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>
<div class="flex items-center mb-2">
	{$t('vnc.column-count')}
	<Dropdown
		values={[
			{ label: '1', value: 1 },
			{ label: '2', value: 2 },
			{ label: '3', value: 3 },
			{ label: '4', value: 4 },
			{ label: '5', value: 5 },
			{ label: '6', value: 6 }
		]}
		showBox={false}
		selected={columns}
		onSelected={(value) => {
			columns = value;
			if (browser) document.cookie = `vnc-displays-per-column=${columns}; SameSite=Lax;`;
			return value;
		}}
		class="min-w-10"
	/>
</div>
<DynamicGrid class={columns === 2 ? 'gap-4' : 'gap-2'} {columns}>
	{#each data.allDeploymentInfos as deploymentInfo}
		{@const config = data.globalState.configs.find(
			(d) => d.identifier === deploymentInfo.deployed_config_id
		)}
		{#if config && targetShouldShowVNC(config, data.globalState)}
			<div>
				<IdentifierLink
					identifier={deploymentInfo.deployed_config_id}
					context="config"
					globalState={data.globalState}
					class="flex justify-center my-2"
				/>
				<VncView globalState={data.globalState} {config} {deploymentInfo} />
			</div>
		{/if}
	{/each}
</DynamicGrid>
