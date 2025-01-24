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
	export let data: PageData;

	const getConfigFromIdentifier = (identifier: string | null) => {
		if (!identifier) return undefined;
		return data.state.devices.find((device) => device.identifier === identifier);
	};
</script>

{#if $globalNavSelectedTargetType === 'config' && $globalNavSelectedConfig}
	<!-- <VncView device={$globalNavSelectedConfig} /> -->
	{#if data.deploymentInfos}
		{#each data.deploymentInfos as deploymentInfo}
			<VncView
				device={getConfigFromIdentifier(deploymentInfo.deployed_config_id)}
				{deploymentInfo}
			/>
		{/each}
	{/if}
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			{#if targetShouldShowVNC(device, $state)}
				{#each data.allDeploymentInfos.get(device.identifier) ?? [] as deploymentInfo}
					<VncView {device} {deploymentInfo} />
				{/each}
			{/if}
		{/each}
	</div>
{/if}
