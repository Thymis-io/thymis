<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import VncColumnPicker from '$lib/vnc/VncColumnPicker.svelte';

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

<div class="ds-filterbar mb-3">
	<VncColumnPicker cookieKey="vnc-displays-per-column" bind:value={columns} />
</div>
<DynamicGrid class="gap-4" {columns}>
	{#each data.deploymentInfos.filter((d) => d.connected) as deploymentInfo (deploymentInfo.id)}
		{@const config = getConfigFromIdentifier(deploymentInfo.deployed_config_id)}
		{@const showVNC = config && targetShouldShowVNC(config, data.globalState)}
		{#if showVNC}
			<VncView globalState={data.globalState} {config} {deploymentInfo} showConfigLink={false} />
		{/if}
	{/each}
</DynamicGrid>
