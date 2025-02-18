<script lang="ts">
	import { t } from 'svelte-i18n';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import { browser } from '$app/environment';

	export let data: PageData;

	let columns = data.vncDisplaysPerColumn;

	const getConfigFromIdentifier = (identifier: string | null) => {
		if (!identifier) return undefined;
		return data.state.configs.find((config) => config.identifier === identifier);
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
	{#if $globalNavSelectedTargetType === 'config' && $globalNavSelectedConfig}
		{#if data.deploymentInfos}
			{#each data.deploymentInfos as deploymentInfo}
				<VncView
					config={getConfigFromIdentifier(deploymentInfo.deployed_config_id)}
					{deploymentInfo}
				/>
			{/each}
		{/if}
	{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
		{#each data.state.configs.filter( (config) => config.tags.includes($globalNavSelectedTag.identifier) ) as config}
			{#if targetShouldShowVNC(config, $state)}
				{#each data.allDeploymentInfos.get(config.identifier) ?? [] as deploymentInfo}
					<VncView {config} {deploymentInfo} />
				{/each}
			{/if}
		{/each}
	{/if}
</DynamicGrid>
