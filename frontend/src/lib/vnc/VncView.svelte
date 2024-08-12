<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Device } from '$lib/state';
	import { state } from '$lib/state';
	import { browser } from '$app/environment';
	import { controllerHost } from '$lib/api';
	import { Card, Spinner } from 'flowbite-svelte';
	import { onDestroy } from 'svelte';
	import { deviceHasVNCModule } from '$lib/vnc/vnc';

	export let device: Device;
	let rfb: any;
	let connected = false;
	let connectionFailed = false;

	$: hasVNC = device && deviceHasVNCModule(device, $state);

	const initVNC = async (device: Device) => {
		// @ts-ignore
		let RFB = await import('@novnc/novnc/lib/rfb.js');

		const url = `ws://${controllerHost}/vnc/${device.identifier}`;

		const password = '';
		const canvas = document.getElementById(`vnc-canvas-${device.targetHost}`);

		if (rfb) {
			rfb.disconnect();
		}

		connected = false;
		connectionFailed = false;

		rfb = new RFB.default(canvas, url, { credentials: { password: password } });
		rfb.addEventListener('connect', () => connected = true);
		rfb.addEventListener('disconnect', () => connectionFailed = true);
		rfb.addEventListener('securityfailure', () => connectionFailed = true);

		rfb.viewOnly = true;
		rfb.scaleViewport = true;
		rfb.showDotCursor = true;
	};

	onDestroy(() => {
		if (rfb) {
			rfb.disconnect();
			rfb = null;
		}
	});

	$: {
		if (browser && hasVNC) {
			initVNC(device);
		}
	}
</script>

{#if hasVNC}
	<Card class="w-full max-w-none">
		<pre>vncviewer {device.targetHost}:5900</pre>
		<div
			id={`vnc-canvas-${device.targetHost}`}
			class="relative w-full aspect-video mt-4"
		>
			{#if connectionFailed}
				<p class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-red-500">
					{$t('vnc.connection-failed')}
				</p>
			{:else if !connected}
				<Spinner size=16 class="absolute top-1/2 left-1/2 -mt-8 -ml-8" />
			{/if}
		</div>
	</Card>
{/if}
