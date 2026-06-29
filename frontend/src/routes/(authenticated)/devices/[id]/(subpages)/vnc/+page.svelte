<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import Section from '$lib/components/layout/Section.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(
		data.globalState.deploymentInfos.find((di) => di.id === data.deploymentInfoId)!
	);
	let config = $derived(
		data.globalState.configs.find((c) => c.identifier === deploymentInfo.deployed_config_id)
	);
	let hasVnc = $derived(!!config && targetShouldShowVNC(config, data.globalState));
</script>

<Section title={$t('nav.device-vnc')}>
	{#if deploymentInfo.connected && hasVnc && config}
		<VncView globalState={data.globalState} {config} {deploymentInfo} embedded />
	{:else}
		<p class="tab-empty">{$t('device-details.not-connected')}</p>
	{/if}
</Section>

<style lang="postcss">
	.tab-empty {
		padding: 24px 4px;
		font-size: 14px;
		color: var(--ds-text-mute);
	}
</style>
