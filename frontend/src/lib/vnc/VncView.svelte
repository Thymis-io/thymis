<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Config, Module } from '$lib/state';
	import { Spinner, Toggle } from 'flowbite-svelte';
	import { onDestroy, onMount } from 'svelte';
	import { configVNCPassword, targetShouldShowVNC } from '$lib/vnc/vnc';
	import { page } from '$app/stores';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import Expand from 'lucide-svelte/icons/expand';
	import Shrink from 'lucide-svelte/icons/shrink';
	import MonitorOff from 'lucide-svelte/icons/monitor-off';

	interface Props {
		globalState: GlobalState;
		config: Config | undefined;
		deploymentInfo: DeploymentInfo;
		/** Show the configuration name in the header (hidden when already in a config context). */
		showConfigLink?: boolean;
	}

	let { globalState, config, deploymentInfo, showConfigLink = true }: Props = $props();

	let rfb: any;
	let connected = $state(false);
	let connectionFailed = $state(false);

	let control = $state(false);
	let isFullscreen = $state(false);

	let hasVNC = $derived(deploymentInfo && config && targetShouldShowVNC(config, globalState));

	let lastDeploymentInfoId = deploymentInfo.id;

	$effect(() => {
		if (hasVNC && deploymentInfo.id !== lastDeploymentInfoId) {
			lastDeploymentInfoId = deploymentInfo.id;
			initVNC(deploymentInfo);
		}
	});

	// keep novnc view-only state in sync with the control toggle
	$effect(() => {
		if (rfb) rfb.viewOnly = !control;
	});

	let div: HTMLDivElement | undefined = $state();

	const initVNC = async (deploymentInfo: DeploymentInfo) => {
		if (!deploymentInfo || !config) {
			return;
		}

		// @ts-ignore
		let RFB = await import('@novnc/novnc/lib/rfb.js');

		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/vnc/${deploymentInfo.id}`;

		const password = configVNCPassword(
			config,
			globalState,
			$page.data.availableModules as Module[]
		);

		if (rfb) {
			rfb.disconnect();
		}

		connected = false;
		connectionFailed = false;

		rfb = new RFB.default(div, url, { credentials: { password: password } });
		rfb.addEventListener('connect', () => {
			connected = true;
			connectionFailed = false;
		});
		rfb.addEventListener('disconnect', () => {
			connected = false;
			connectionFailed = true;
		});
		rfb.addEventListener('securityfailure', () => {
			connected = false;
			connectionFailed = true;
		});

		rfb.viewOnly = !control;
		rfb.scaleViewport = true;
		rfb.showDotCursor = true;
	};

	const reconnect = () => {
		if (hasVNC) initVNC(deploymentInfo);
	};

	const toggleFullscreen = () => {
		if (!div) return;
		if (document.fullscreenElement) {
			document.exitFullscreen();
		} else {
			div.requestFullscreen?.();
		}
	};

	const onFullscreenChange = () => {
		isFullscreen = document.fullscreenElement === div;
	};

	onMount(() => {
		document.addEventListener('fullscreenchange', onFullscreenChange);
		if (hasVNC) {
			initVNC(deploymentInfo);
		}
	});

	onDestroy(() => {
		document.removeEventListener('fullscreenchange', onFullscreenChange);
		if (rfb) {
			rfb.disconnect();
			rfb = null;
		}
	});
</script>

{#if hasVNC}
	<div class="vnc-card">
		<div class="vnc-head">
			<div class="vnc-identity">
				{#if showConfigLink}
					<IdentifierLink
						{globalState}
						{deploymentInfo}
						identifier={deploymentInfo.deployed_config_id}
						context="config"
						iconSize="0.95rem"
						class="vnc-config-link"
					/>
				{/if}
				<IdentifierLink
					{globalState}
					{deploymentInfo}
					identifier={deploymentInfo.id}
					context="device"
					iconSize="0.8rem"
					class="vnc-device-link"
				/>
			</div>
			<div class="vnc-controls">
				<span
					class="ds-status-pill {connectionFailed ? 'danger' : connected ? 'online' : 'offline'}"
				>
					<span class="ds-dot"></span>
					{connectionFailed
						? $t('vnc.disconnected')
						: connected
							? $t('vnc.live')
							: $t('vnc.connecting')}
				</span>
				<label class="vnc-toggle" class:disabled={!connected}>
					<span>{$t('vnc.control-device')}</span>
					<Toggle bind:checked={control} size="small" disabled={!connected} />
				</label>
			</div>
		</div>

		<!-- novnc mounts its canvas into this element; overlays sit on top -->
		<div bind:this={div} class="vnc-screen" class:fullscreen={isFullscreen}>
			{#if connectionFailed}
				<div class="vnc-overlay">
					<MonitorOff size={26} />
					<span>{$t('vnc.connection-failed')}</span>
					<button type="button" class="vnc-retry" onclick={reconnect}>{$t('vnc.retry')}</button>
				</div>
			{:else if !connected}
				<div class="vnc-overlay">
					<Spinner size="6" />
					<span>{$t('vnc.connecting')}</span>
				</div>
			{/if}

			<button
				type="button"
				class="vnc-expand"
				onclick={toggleFullscreen}
				title={$t('vnc.fullscreen')}
				aria-label={$t('vnc.fullscreen')}
			>
				{#if isFullscreen}
					<Shrink size={15} />
				{:else}
					<Expand size={15} />
				{/if}
			</button>
		</div>
	</div>
{/if}

<style lang="postcss">
	.vnc-card {
		display: flex;
		flex-direction: column;
		background: var(--ds-surface);
		border: 1px solid var(--ds-border);
		border-radius: var(--ds-radius-lg);
		box-shadow: var(--ds-shadow-md);
		overflow: hidden;
	}

	/* ---- header ---- */
	.vnc-head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
		padding: 10px 12px;
	}
	.vnc-identity {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	.vnc-identity :global(.vnc-config-link a) {
		font-size: 13.5px;
		font-weight: 600;
		color: var(--ds-text);
	}
	.vnc-identity :global(.vnc-device-link) {
		min-width: 0;
		max-width: 100%;
	}
	.vnc-identity :global(.vnc-device-link a) {
		font-size: 11px;
		color: var(--ds-text-mute);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 100%;
	}

	.vnc-controls {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 7px;
		flex-shrink: 0;
	}
	.vnc-toggle {
		display: flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		color: var(--ds-text-dim);
		cursor: pointer;
	}
	.vnc-toggle.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* ---- screen ---- */
	.vnc-screen {
		position: relative;
		width: 100%;
		aspect-ratio: 16 / 9;
		background: radial-gradient(120% 120% at 50% 0%, #11161f 0%, #06080c 100%);
		border-top: 1px solid var(--ds-border);
		overflow: hidden;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.vnc-screen.fullscreen {
		aspect-ratio: auto;
		height: 100%;
	}
	/* the canvas novnc injects */
	.vnc-screen :global(canvas) {
		display: block;
		max-width: 100%;
		max-height: 100%;
	}

	.vnc-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 10px;
		color: var(--ds-text-mute);
		font-size: 12.5px;
		pointer-events: none;
	}
	.vnc-overlay :global(svg) {
		opacity: 0.8;
	}
	.vnc-retry {
		pointer-events: auto;
		margin-top: 2px;
		padding: 4px 12px;
		border-radius: 999px;
		font-size: 12px;
		font-weight: 500;
		color: var(--ds-text);
		background: rgba(255, 255, 255, 0.08);
		border: 1px solid rgba(255, 255, 255, 0.14);
		transition: background 0.12s;
	}
	.vnc-retry:hover {
		background: rgba(255, 255, 255, 0.16);
	}

	.vnc-expand {
		position: absolute;
		top: 8px;
		right: 8px;
		display: grid;
		place-items: center;
		width: 28px;
		height: 28px;
		border-radius: 7px;
		color: #fff;
		background: rgba(10, 13, 19, 0.55);
		border: 1px solid rgba(255, 255, 255, 0.12);
		backdrop-filter: blur(4px);
		opacity: 0;
		transition:
			opacity 0.15s,
			background 0.12s;
	}
	.vnc-screen:hover .vnc-expand,
	.vnc-expand:focus-visible {
		opacity: 1;
	}
	.vnc-expand:hover {
		background: rgba(10, 13, 19, 0.8);
	}
</style>
