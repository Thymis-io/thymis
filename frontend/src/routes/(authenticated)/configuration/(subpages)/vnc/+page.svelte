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
	import { queryParam } from 'sveltekit-search-params';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';

	export let data: PageData;

	$: columnsParam = queryParam('vnc-config-columns');
	$: columns = parseInt($columnsParam ?? '2');

	const getConfigFromIdentifier = (identifier: string | null) => {
		if (!identifier) return undefined;
		return data.state.devices.find((device) => device.identifier === identifier);
	};
</script>

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
	{#if $globalNavSelectedTargetType === 'config' && $globalNavSelectedConfig}
		{#if data.deploymentInfos}
			{#each data.deploymentInfos as deploymentInfo}
				<VncView
					device={getConfigFromIdentifier(deploymentInfo.deployed_config_id)}
					{deploymentInfo}
				/>
			{/each}
		{/if}
	{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			{#if targetShouldShowVNC(device, $state)}
				{#each data.allDeploymentInfos.get(device.identifier) ?? [] as deploymentInfo}
					<VncView {device} {deploymentInfo} />
				{/each}
			{/if}
		{/each}
	{/if}
</DynamicGrid>
