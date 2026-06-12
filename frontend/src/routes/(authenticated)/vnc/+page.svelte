<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import { browser } from '$app/environment';
	import ScreenShare from 'lucide-svelte/icons/screen-share';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let columns = $state(data.vncDisplaysPerColumn);

	let vncDevices = $derived(
		data.allDeploymentInfos
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
		<span style="color: var(--ds-text-dim); font-size: 13px;">{$t('vnc.column-count')}</span>
		<Dropdown
			values={[
				{ label: '1', value: 1 },
				{ label: '2', value: 2 },
				{ label: '3', value: 3 },
				{ label: '4', value: 4 },
				{ label: '5', value: 5 },
				{ label: '6', value: 6 }
			]}
			showBox={false}
			selected={columns}
			onSelected={(value) => {
				columns = value;
				if (browser) document.cookie = `vnc-displays-per-column=${columns}; SameSite=Lax;`;
				return value;
			}}
			class="min-w-10"
		/>
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
