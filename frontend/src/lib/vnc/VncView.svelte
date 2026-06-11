<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Config, Module } from '$lib/state';
	import { Spinner, Toggle } from 'flowbite-svelte';
	import { onDestroy, onMount } from 'svelte';
	import { configVNCPassword, targetShouldShowVNC } from '$lib/vnc/vnc';
	import { page } from '$app/stores';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		config: Config | undefined;
		deploymentInfo: DeploymentInfo;
	}

	let { globalState, config, deploymentInfo }: Props = $props();

	let rfb: any;
	let connected = $state(false);
	let connectionFailed = $state(false);

	let control = $state(false);

	let hasVNC = $derived(deploymentInfo && config && targetShouldShowVNC(config, globalState));

	let lastDeploymentInfoId = deploymentInfo.id;

	$effect(() => {
		if (hasVNC && deploymentInfo.id !== lastDeploymentInfoId) {
			lastDeploymentInfoId = deploymentInfo.id;
			initVNC(deploymentInfo);
		}
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

	const toggleControl = () => {
		control = !control;

		if (rfb) {
			rfb.viewOnly = !control;
		}
	};

	onMount(() => {
		if (hasVNC) {
			initVNC(deploymentInfo);
		}
	});

	onDestroy(() => {
		if (rfb) {
			rfb.disconnect();
			rfb = null;
		}
	});
</script>

{#if hasVNC}
	<div class="ds-card w-full">
		<div class="ds-card-head">
			<span class="ds-status-pill {connectionFailed ? 'danger' : connected ? 'online' : 'offline'}">
				<span class="ds-dot"></span>
				{connectionFailed
					? $t('vnc.disconnected')
					: connected
						? $t('vnc.live')
						: $t('vnc.connecting')}
			</span>
			<label class="flex items-center gap-2" style="color: var(--ds-text-dim); font-size: 13px;">
				{$t('vnc.control-device')}
				<Toggle bind:checked={control} class="mr-[-10px]" size="small" on:click={toggleControl} />
			</label>
		</div>
		<div class="ds-card-pad">
			<div bind:this={div} class="relative w-full aspect-video">
				{#if connectionFailed}
					<p
						class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
						style="color: var(--ds-danger);"
					>
						{$t('vnc.connection-failed')}
					</p>
				{:else if !connected}
					<Spinner size="16" class="absolute top-1/2 left-1/2 -mt-8 -ml-8" />
				{/if}
			</div>
		</div>
	</div>
{/if}
