<script lang="ts">
	import { Xterm, XtermAddon } from '@battlefieldduck/xterm-svelte';
	import type {
		ITerminalOptions,
		ITerminalInitOnlyOptions,
		Terminal
	} from '@battlefieldduck/xterm-svelte';
	import { globalNavSelectedDevice, type Device } from '$lib/state';

	$: device = $globalNavSelectedDevice;

	let terminal: Terminal;
	let ws: WebSocket;

	const options: ITerminalOptions & ITerminalInitOnlyOptions = {
		cursorBlink: true
	};

	async function onLoad(event: CustomEvent<{ terminal: Terminal }>) {
		terminal = event.detail.terminal;
	}

	const initTerminal = async (device: Device, terminal: Terminal) => {
		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/terminal/${device.identifier}`;
		ws = new WebSocket(url);

		const fitAddon = new (await XtermAddon.FitAddon()).FitAddon();
		const attachAddon = new (await XtermAddon.AttachAddon()).AttachAddon(ws);
		terminal.loadAddon(fitAddon);
		terminal.loadAddon(attachAddon);
		fitAddon.fit();
	};

	$: {
		terminal?.reset();
		ws?.close();

		if (device && terminal) {
			initTerminal(device, terminal);
		}
	}
</script>

<Xterm {options} on:load={onLoad} />
