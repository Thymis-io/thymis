<script lang="ts">
	import { t } from 'svelte-i18n';
	import { P } from 'flowbite-svelte';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTarget,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import { getDeploymentInfosByConfigId } from '$lib/deploymentInfo';

	import type { PageData } from '../../$types';
	export let data: PageData;

	const getConfigFromIdentifier = (identifier: string) => {
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
