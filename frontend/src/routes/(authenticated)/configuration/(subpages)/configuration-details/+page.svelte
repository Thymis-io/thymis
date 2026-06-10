<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionActions from './SectionActions.svelte';
	import SectionDanger from './SectionDanger.svelte';
	import SectionDeploymentInfo from './SectionDeploymentInfo.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from './Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let currentConfig = $derived(data.nav.selectedConfig);
</script>

{#if data.nav.selectedConfig}
	<div class="grid grid-cols-4 grid-flow-row gap-4">
		<SectionDeploymentInfo
			class="col-span-3"
			deploymentInfos={data.deploymentInfos}
			globalState={data.globalState}
			headCommit={data.headCommit}
			repoStatus={data.repoStatus}
		/>
		<SectionActions class="col-span-1" config={data.nav.selectedConfig} />
		<SectionConfiguration
			globalState={data.globalState}
			class="col-span-3"
			config={data.nav.selectedConfig}
			availableModules={data.availableModules}
		/>
		<SectionDanger
			class="col-span-1"
			config={data.nav.selectedConfig}
			globalState={data.globalState}
		/>
		{#each data.connectedDeploymentInfos as deploymentInfo}
			{#if targetShouldShowVNC(currentConfig, data.globalState)}
				<Section class="col-span-2" title={$t('nav.device-vnc')}>
					{#snippet header()}
						<IdentifierLink
							globalState={data.globalState}
							deploymentInfos={data.deploymentInfos}
							identifier={deploymentInfo.id}
							context="device"
							class="flex justify-center my-1"
						/>
					{/snippet}
					<VncView globalState={data.globalState} config={currentConfig} {deploymentInfo} />
				</Section>
			{/if}
			<Section class="col-span-2" title={$t('nav.terminal')}>
				{#snippet header()}
					<IdentifierLink
						globalState={data.globalState}
						deploymentInfos={data.deploymentInfos}
						identifier={deploymentInfo.id}
						context="device"
						class="flex justify-center my-1"
					/>
				{/snippet}
				<Terminal {deploymentInfo} />
			</Section>
		{/each}
	</div>
{:else if data.nav.selectedTag}
	<div></div>
{/if}
