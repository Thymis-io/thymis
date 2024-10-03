<script lang="ts">
	import { Xterm, XtermAddon } from '@battlefieldduck/xterm-svelte';
	import type {
		ITerminalOptions,
		ITerminalInitOnlyOptions,
		Terminal
	} from '@battlefieldduck/xterm-svelte';
	import { globalNavSelectedDevice, type Device } from '$lib/state';
	import { onDestroy, onMount } from 'svelte';

	$: device = $globalNavSelectedDevice;

	let terminal: Terminal;
	let ws: WebSocket;

	const options: ITerminalOptions & ITerminalInitOnlyOptions = {
		cursorBlink: true,
		letterSpacing: 0
	};

	const onLoad = (event: CustomEvent<{ terminal: Terminal }>) => {
		terminal = event.detail.terminal;
	};

	const initTerminal = async (device: Device, terminal: Terminal) => {
		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/terminal/${device.identifier}`;
		ws = new WebSocket(url);

		const fitAddon = new (await XtermAddon.FitAddon()).FitAddon();
		terminal.loadAddon(fitAddon);
		fitAddon.fit();

		const observer = new ResizeObserver(() => {
			fitAddon?.fit();
		});
		if (terminal.element) observer.observe(terminal.element);

		const attachAddon = new (await XtermAddon.AttachAddon()).AttachAddon(ws);
		terminal.loadAddon(attachAddon);

		terminal.writeln(`Connecting to ${device.displayName}...`);
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

<Xterm {options} on:load={onLoad} class="w-full h-full" />
