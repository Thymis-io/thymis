<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionDeploymentInfo from './SectionDeploymentInfo.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from '$lib/components/layout/Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import CopySSHCommandButton from '$lib/terminal/CopySSHCommandButton.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let currentConfig = $derived(data.nav.selectedConfig);
</script>

{#if data.nav.selectedConfig}
	<div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
		<SectionConfiguration
			globalState={data.globalState}
			class="lg:col-span-1"
			config={data.nav.selectedConfig}
			availableModules={data.availableModules}
		/>
		<SectionDeploymentInfo
			class="lg:col-span-1"
			deploymentInfos={data.deploymentInfos}
			globalState={data.globalState}
			headCommit={data.headCommit}
		/>

		{#each data.connectedDeploymentInfos as deploymentInfo}
			{#if targetShouldShowVNC(currentConfig, data.globalState)}
				<Section class="lg:col-span-1" title={$t('nav.device-vnc')}>
					{#snippet header()}
						<IdentifierLink
							globalState={data.globalState}
							deploymentInfos={data.deploymentInfos}
							identifier={deploymentInfo.id}
							context="device"
							class="flex justify-center my-1"
						/>
					{/snippet}
					<VncView
						globalState={data.globalState}
						config={currentConfig}
						{deploymentInfo}
						embedded
					/>
				</Section>
			{/if}
			<Section class="lg:col-span-1" title={$t('nav.terminal')}>
				{#snippet header()}
					<div class="flex items-center gap-3">
						<IdentifierLink
							globalState={data.globalState}
							deploymentInfos={data.deploymentInfos}
							identifier={deploymentInfo.id}
							context="device"
							class="flex justify-center my-1"
						/>
						<CopySSHCommandButton {deploymentInfo} />
					</div>
				{/snippet}
				<Terminal {deploymentInfo} />
			</Section>
		{/each}
	</div>
{:else if data.nav.selectedTag}
	<div></div>
{/if}
