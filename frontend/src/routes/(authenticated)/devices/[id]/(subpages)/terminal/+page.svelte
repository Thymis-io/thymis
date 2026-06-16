<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import CopySSHCommandButton from '$lib/terminal/CopySSHCommandButton.svelte';
	import Section from '$lib/components/layout/Section.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(data.deploymentInfo);
</script>

<Section title={$t('nav.terminal')}>
	{#snippet header()}
		{#if data.connected}
			<CopySSHCommandButton {deploymentInfo} />
		{/if}
	{/snippet}
	{#if data.connected}
		<Terminal {deploymentInfo} />
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
