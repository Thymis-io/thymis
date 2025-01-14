<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Badge, Card } from 'flowbite-svelte';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionActions from './SectionActions.svelte';
	import SectionDanger from './SectionDanger.svelte';
	import SectionDeploymentInfo from './SectionDeploymentInfo.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from './Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import Tabbar from '$lib/components/Tabbar.svelte';

	export let data: PageData;

	$: currentDevice = $globalNavSelectedConfig;
</script>

{#if $globalNavSelectedTargetType === 'config' && currentDevice}
	<div class="grid grid-cols-4 grid-flow-row gap-x-2 gap-y-6">
		<SectionDeploymentInfo
			class="col-span-3"
			deploymentInfos={data.deploymentInfos}
			device={currentDevice}
		/>
		<SectionActions class="col-span-1" device={currentDevice} />
		<SectionConfiguration
			class="col-span-3"
			device={currentDevice}
			availableModules={data.availableModules}
		/>
		<SectionDanger class="col-span-1" device={currentDevice} />
		{#if targetShouldShowVNC(currentDevice, $state)}
			{#each data.deploymentInfos as deploymentInfo}
				<Section
					class="col-span-2"
					title="{$t('nav.device-vnc')} {deploymentInfo.reachable_deployed_host}"
				>
					<VncView device={currentDevice} {deploymentInfo} />
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
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<p>Test</p>
		{/each}
	</div>
{/if}
