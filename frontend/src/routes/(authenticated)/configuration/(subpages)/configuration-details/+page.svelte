<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Card } from 'flowbite-svelte';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionActions from './SectionActions.svelte';
	import SectionDanger from './SectionDanger.svelte';
	import SectionDeploymentInfo from './SectionDeploymentInfo.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from './Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let currentConfig = $derived(data.nav.selectedConfig);
</script>

{#if data.nav.selectedConfig}
	<div class="grid grid-cols-4 grid-flow-row gap-x-2 gap-y-6">
		<SectionDeploymentInfo
			class="col-span-3"
			deploymentInfos={data.connectedDeploymentInfos}
			config={data.nav.selectedConfig}
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
		{#if targetShouldShowVNC(currentConfig, data.globalState)}
			{#each data.connectedDeploymentInfos as deploymentInfo}
				<Section class="col-span-2" title={$t('nav.device-vnc')}>
					<VncView globalState={data.globalState} config={currentConfig} {deploymentInfo} />
				</Section>
			{/each}
		{/if}
		{#each data.connectedDeploymentInfos as deploymentInfo}
			<Section class="col-span-2" title={$t('nav.terminal')}>
				<Card class="w-full max-w-none" padding="sm">
					<Terminal {deploymentInfo} />
				</Card>
			</Section>
		{/each}
	</div>
{:else if data.nav.selectedTag}
	<div></div>
{/if}
