<script lang="ts">
	import type { PageData } from './$types';
	import { P, Card } from 'flowbite-svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { state, type Device } from '$lib/state';
	import { browser } from '$app/environment';
	import { controllerHost } from '$lib/api';

	const initVNC = async (device: Device) => {
		// @ts-ignore
		let RFB = await import('@novnc/novnc/lib/rfb.js');

		const url = `ws://${controllerHost}/vnc/${device.identifier}`;

		const password = '';
		const canvas = document.getElementById(`vnc-canvas-${device.targetHost}`);
		const rfb = new RFB.default(canvas, url, { credentials: { password: password } });

		rfb.viewOnly = true;
		rfb.scaleViewport = true;
		rfb.showDotCursor = true;
	};

	if (browser) {
		for (const device of $state.devices) {
			initVNC(device);
		}
	}

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<div />
	<DeployActions />
</div>
<div class="grid grid-cols-3 gap-4">
	{#each $state.devices as device}
		<div>
			<P class="mb-2 text-center">{device.displayName}</P>
			<Card class="w-full max-w-none">
				<pre>vncviewer {device.targetHost}:5900</pre>
				<div id={`vnc-canvas-${device.targetHost}`} class="w-full aspect-video mt-4" />
			</Card>
		</div>
	{/each}
</div>
