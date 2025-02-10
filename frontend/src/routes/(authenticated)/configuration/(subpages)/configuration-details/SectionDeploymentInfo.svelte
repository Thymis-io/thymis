<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import type { Config } from '$lib/state';
	import EditDeploymentInfo from '$lib/EditDeploymentInfo.svelte';

	export let deploymentInfos: DeploymentInfo[] = [];
	export let config: Config;

	let className = '';
	export { className as class };

	let editDeploymentInfoModalOpen = false;

	let currentDeploymentInfo: DeploymentInfo | undefined = deploymentInfos?.[0];
</script>

<EditDeploymentInfo
	bind:deploymentInfo={currentDeploymentInfo}
	bind:open={editDeploymentInfoModalOpen}
	configIdentifier={config.identifier}
/>
<Section class={className} title={$t('configuration-details.deployment-info')}>
	<div class="flex flex-col gap-2">
		{#each deploymentInfos as deploymentInfo}
			{#if deploymentInfo}
				<div class="grid grid-cols-[max-content_max-content_max-content_1fr] gap-x-2">
					<p class="break-all text-base">{$t('configuration-details.deployed-at')}:</p>
					<p class="break-all text-base">
						{deploymentInfo.reachable_deployed_host},
						{deploymentInfo.deployed_config_commit?.slice(0, 8) ??
							$t('configuration-details.no-commit')}
					</p>
				</div>
			{/if}
		{:else}
			<p class="text-base">{$t('configuration-details.no-deployment-info')}</p>
		{/each}
	</div>
</Section>
