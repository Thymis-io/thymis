<script lang="ts">
	import '@xterm/xterm/css/xterm.css';
	import { type Device } from '$lib/state';
	import { onDestroy, onMount } from 'svelte';
	import { Terminal, type ITerminalInitOnlyOptions, type ITerminalOptions } from '@xterm/xterm';
	import { AttachAddon } from '@xterm/addon-attach';
	import { FitAddon } from '@xterm/addon-fit';
	import { WebglAddon } from '@xterm/addon-webgl';

	export let device: Device | undefined;

	let terminal: Terminal;
	let divElement: HTMLDivElement;
	let ws: WebSocket;

	const options: ITerminalOptions & ITerminalInitOnlyOptions = {
		cursorBlink: true,
		letterSpacing: 0
	};

	onMount(() => {
		terminal = new Terminal(options);
		terminal.open(divElement);
	});

	const initTerminal = async (device: Device, terminal: Terminal) => {
		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/terminal/${device.identifier}`;
		ws = new WebSocket(url);

		const fitAddon = new FitAddon();
		terminal.loadAddon(fitAddon);
		fitAddon.fit();

		const observer = new ResizeObserver(() => {
			fitAddon?.fit();
			const dims = fitAddon.proposeDimensions();
			ws.send(`\x04${JSON.stringify(dims)}`);
		});
		if (terminal.element) observer.observe(terminal.element);

		const webglAddon = new WebglAddon();
		terminal.loadAddon(webglAddon);

		terminal.writeln(`Connecting to ${device.displayName}...`);
		const attachAddon = new AttachAddon(ws);
		terminal.loadAddon(attachAddon);
	};

	const resetConnection = () => {
		terminal?.reset();
		ws?.close();
	};

	onDestroy(() => {
		resetConnection();
	});

	$: {
		resetConnection();

		if (device && terminal) {
			initTerminal(device, terminal);
		}
	}
</script>

<div class="w-full h-full" bind:this={divElement}></div>
