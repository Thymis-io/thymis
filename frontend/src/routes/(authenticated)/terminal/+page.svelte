<script lang="ts">
	import { Xterm, XtermAddon } from '@battlefieldduck/xterm-svelte';
	import type {
		ITerminalOptions,
		ITerminalInitOnlyOptions,
		Terminal
	} from '@battlefieldduck/xterm-svelte';
	import { globalNavSelectedDevice } from '$lib/state';

	$: device = $globalNavSelectedDevice;

	let terminal: Terminal;

	const options: ITerminalOptions & ITerminalInitOnlyOptions = {
		cursorBlink: true,
		convertEol: true
	};

	async function onLoad(event: CustomEvent<{ terminal: Terminal }>) {
		if (!device) {
			return;
		}

		terminal = event.detail.terminal;
		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/terminal/${device.identifier}`;
		const ws = new WebSocket(url);

		const fitAddon = new (await XtermAddon.FitAddon()).FitAddon();
		const attachAddon = new (await XtermAddon.AttachAddon()).AttachAddon(ws);
		terminal.loadAddon(fitAddon);
		terminal.loadAddon(attachAddon);
		fitAddon.fit();
	}
</script>

<Xterm {options} on:load={onLoad} />
