<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Card } from 'flowbite-svelte';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionActions from './SectionActions.svelte';
	import SectionDanger from './SectionDanger.svelte';
	import SectionDeploymentInfo from './SectionDeploymentInfo.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from './Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';

	export let data: PageData;

	$: currentConfig = $globalNavSelectedConfig;
</script>

{#if $globalNavSelectedTargetType === 'config' && currentConfig}
	<div class="grid grid-cols-4 grid-flow-row gap-x-2 gap-y-6">
		<SectionDeploymentInfo
			class="col-span-3"
			deploymentInfos={data.deploymentInfos}
			config={currentConfig}
		/>
		<SectionActions class="col-span-1" config={currentConfig} />
		<SectionConfiguration
			class="col-span-3"
			config={currentConfig}
			availableModules={data.availableModules}
		/>
		<SectionDanger class="col-span-1" config={currentConfig} />
		{#if targetShouldShowVNC(currentConfig, $state)}
			{#each data.deploymentInfos as deploymentInfo}
				<Section class="col-span-2" title={$t('nav.device-vnc')}>
					<VncView config={currentConfig} {deploymentInfo} />
				</Section>
			{/each}
		{/if}
		{#each data.deploymentInfos as deploymentInfo}
			<Section class="col-span-2" title={$t('nav.terminal')}>
				<Card class="w-full max-w-none" padding="sm">
					<Terminal {deploymentInfo} />
				</Card>
			</Section>
		{/each}
	</div>
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}{/if}
