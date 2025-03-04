<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Config, Module } from '$lib/state';
	import { globalState } from '$lib/state';
	import { Card, Spinner, Toggle, P } from 'flowbite-svelte';
	import { onDestroy, onMount } from 'svelte';
	import { configVNCPassword, targetShouldShowVNC } from '$lib/vnc/vnc';
	import { page } from '$app/stores';
	import { type DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		config: Config | undefined;
		deploymentInfo: DeploymentInfo;
	}

	let { config, deploymentInfo }: Props = $props();
	let deviceHost: string;
	let rfb: any;
	let connected = $state(false);
	let connectionFailed = $state(false);

	let control = $state(false);

	let hasVNC = $derived(deploymentInfo && config && targetShouldShowVNC(config, $globalState));

	let div: HTMLDivElement = $state();

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
			$globalState,
			$page.data.availableModules as Module[]
		);

		if (rfb) {
			rfb.disconnect();
		}

		connected = false;
		connectionFailed = false;

		rfb = new RFB.default(div, url, { credentials: { password: password } });
		rfb.addEventListener('connect', () => (connected = true));
		rfb.addEventListener('disconnect', () => (connectionFailed = true));
		rfb.addEventListener('securityfailure', () => (connectionFailed = true));

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
	<Card class="w-full max-w-none" padding="sm">
		<div class="flex flex-wrap justify-between h-12 content-start gap-2">
			<pre class="text-base"></pre>
			<div class="flex items-center gap-2">
				<P>{$t('vnc.control-device')}</P>
				<Toggle bind:checked={control} class="mr-[-10px]" size="small" on:click={toggleControl} />
			</div>
		</div>
		<div bind:this={div} class="relative w-full aspect-video mt-4">
			{#if connectionFailed}
				<p
					class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-red-500"
				>
					{$t('vnc.connection-failed')}
				</p>
			{:else if !connected}
				<Spinner size="16" class="absolute top-1/2 left-1/2 -mt-8 -ml-8" />
			{/if}
		</div>
	</Card>
{/if}
