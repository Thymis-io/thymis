<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Device, Module } from '$lib/state';
	import { state } from '$lib/state';
	import { Card, Spinner, Toggle, P } from 'flowbite-svelte';
	import { onDestroy, onMount } from 'svelte';
	import { deviceVNCPassword, targetShouldShowVNC } from '$lib/vnc/vnc';
	import { page } from '$app/stores';
	import { type DeploymentInfo } from '$lib/deploymentInfo';

	export let device: Device | undefined;
	export let deploymentInfo: DeploymentInfo;
	let deviceHost: string;
	let rfb: any;
	let connected = false;
	let connectionFailed = false;

	let controlDevice = false;

	$: hasVNC = deploymentInfo && device && targetShouldShowVNC(device, $state);

	let div: HTMLCanvasElement;

	const initVNC = async (deploymentInfo: DeploymentInfo) => {
		if (!deploymentInfo || !device) {
			return;
		}

		// @ts-ignore
		let RFB = await import('@novnc/novnc/lib/rfb.js');

		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/vnc/${deploymentInfo.id}`;

		const password = deviceVNCPassword(device, $state, $page.data.availableModules as Module[]);
		const canvas = document.getElementById(`vnc-canvas-${deploymentInfo.id}`);

		if (rfb) {
			rfb.disconnect();
		}

		connected = false;
		connectionFailed = false;

		rfb = new RFB.default(div, url, { credentials: { password: password } });
		rfb.addEventListener('connect', () => (connected = true));
		rfb.addEventListener('disconnect', () => (connectionFailed = true));
		rfb.addEventListener('securityfailure', () => (connectionFailed = true));

		rfb.viewOnly = !controlDevice;
		rfb.scaleViewport = true;
		rfb.showDotCursor = true;
	};

	const toggleControlDevice = () => {
		controlDevice = !controlDevice;

		if (rfb) {
			rfb.viewOnly = !controlDevice;
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
			<pre class="text-base">vncviewer {deploymentInfo?.reachable_deployed_host}:5900</pre>
			<div class="flex items-center gap-2">
				<P>{$t('vnc.control-device')}</P>
				<Toggle
					bind:checked={controlDevice}
					class="mr-[-10px]"
					size="small"
					on:click={toggleControlDevice}
				/>
			</div>
		</div>
		<div
			bind:this={div}
			id={`vnc-canvas-${deploymentInfo.id}`}
			class="relative w-full aspect-video mt-4"
		>
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
