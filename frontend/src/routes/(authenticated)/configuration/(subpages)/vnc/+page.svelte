<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import { browser } from '$app/environment';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let columns = $state(data.vncDisplaysPerColumn);

	const getConfigFromIdentifier = (identifier: string | null) => {
		if (!identifier) return undefined;
		return data.globalState.configs.find((config) => config.identifier === identifier);
	};
</script>

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
	{#each data.deploymentInfos as deploymentInfo}
		{@const config = getConfigFromIdentifier(deploymentInfo.deployed_config_id)}
		{@const showVNC = config && targetShouldShowVNC(config, data.globalState)}
		{#if showVNC}
			<VncView globalState={data.globalState} {config} {deploymentInfo} />
		{/if}
	{/each}
</DynamicGrid>
