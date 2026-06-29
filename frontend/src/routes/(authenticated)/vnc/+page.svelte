<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import VncColumnPicker from '$lib/vnc/VncColumnPicker.svelte';
	import ScreenShare from 'lucide-svelte/icons/screen-share';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let columns = $state(data.vncDisplaysPerColumn);

	let vncDevices = $derived(
		data.globalState.deploymentInfos
			.filter((di) => !di.archived)
			.map((deploymentInfo) => ({
				deploymentInfo,
				config: data.globalState.configs.find(
					(d) => d.identifier === deploymentInfo.deployed_config_id
				)
			}))
			.filter(({ config }) => config && targetShouldShowVNC(config, data.globalState))
	);
</script>

<PageHead title={$t('nav.global-vnc')} subtitle={$t('vnc.subtitle')} />

{#if vncDevices.length > 0}
	<div class="ds-filterbar mb-4">
		<VncColumnPicker cookieKey="vnc-displays-per-column" bind:value={columns} />
	</div>
	<DynamicGrid class="gap-4" {columns}>
		{#each vncDevices as { deploymentInfo, config } (deploymentInfo.id)}
			<VncView globalState={data.globalState} {config} {deploymentInfo} />
		{/each}
	</DynamicGrid>
{:else}
	<div class="ds-empty">
		<div class="ds-empty-icon"><ScreenShare size={26} /></div>
		<p class="ds-empty-title">{$t('vnc.no-devices')}</p>
		<p class="ds-empty-hint">{$t('vnc.no-devices-hint')}</p>
	</div>
{/if}

<style lang="postcss">
	.ds-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 6px;
		padding: 64px 24px;
		text-align: center;
	}
	.ds-empty-icon {
		display: grid;
		place-items: center;
		width: 52px;
		height: 52px;
		margin-bottom: 8px;
		border-radius: 14px;
		color: var(--ds-text-mute);
		background: var(--ds-surface-3);
		border: 1px solid var(--ds-border);
	}
	.ds-empty-title {
		font-size: 15px;
		font-weight: 600;
		color: var(--ds-text);
	}
	.ds-empty-hint {
		font-size: 13px;
		color: var(--ds-text-dim);
		max-width: 360px;
	}
</style>
