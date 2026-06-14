<script lang="ts">
	import { t } from 'svelte-i18n';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import DynamicGrid from '$lib/components/DynamicGrid.svelte';
	import { browser } from '$app/environment';
	import ScreenShare from 'lucide-svelte/icons/screen-share';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const columnOptions = [1, 2, 3, 4, 5, 6];
	let columns = $state(data.vncDisplaysPerColumn);

	const setColumns = (value: number) => {
		columns = value;
		if (browser) document.cookie = `vnc-displays-per-column=${value}; SameSite=Lax;`;
	};

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
		<span class="cols-label">{$t('vnc.column-count')}</span>
		<div class="cols-seg" role="group" aria-label={$t('vnc.column-count')}>
			{#each columnOptions as value (value)}
				<button
					type="button"
					class="cols-seg-btn"
					class:active={columns === value}
					aria-pressed={columns === value}
					onclick={() => setColumns(value)}
				>
					{value}
				</button>
			{/each}
		</div>
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
	.cols-label {
		color: var(--ds-text-dim);
		font-size: 13px;
	}
	/* segmented control for choosing how many displays per row */
	.cols-seg {
		display: inline-flex;
		padding: 2px;
		gap: 2px;
		border-radius: 9px;
		background: var(--ds-surface-3);
		border: 1px solid var(--ds-border);
	}
	.cols-seg-btn {
		min-width: 30px;
		height: 26px;
		padding: 0 8px;
		border-radius: 7px;
		font-size: 13px;
		font-weight: 500;
		color: var(--ds-text-dim);
		background: transparent;
		transition:
			background 0.12s,
			color 0.12s,
			box-shadow 0.12s;
	}
	.cols-seg-btn:hover:not(.active) {
		color: var(--ds-text);
		background: var(--ds-surface);
	}
	.cols-seg-btn.active {
		color: var(--ds-text);
		background: var(--ds-surface);
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
	}
	.cols-seg-btn:focus-visible {
		outline: none;
		box-shadow: 0 0 0 2px var(--ds-accent-dim);
	}

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
