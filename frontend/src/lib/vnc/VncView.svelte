<script lang="ts">
	import type { Device } from '$lib/state';
	import { state } from '$lib/state';
	import { browser } from '$app/environment';
	import { controllerHost } from '$lib/api';
	import { Card } from 'flowbite-svelte';
	import { onDestroy } from 'svelte';
	import { deviceHasVNCModule } from '$lib/vnc/vnc';

	export let device: Device;
	let rfb: any;

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

		rfb = new RFB.default(canvas, url, { credentials: { password: password } });

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
		<div id={`vnc-canvas-${device.targetHost}`} class="w-full aspect-video mt-4" />
	</Card>
{/if}
