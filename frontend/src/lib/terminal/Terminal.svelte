<script lang="ts">
	import { run } from 'svelte/legacy';

	import '@xterm/xterm/css/xterm.css';
	import { onDestroy, onMount } from 'svelte';
	import type { ITerminalInitOnlyOptions, ITerminalOptions } from '@xterm/xterm';
	import type { Terminal as TerminalType } from '@xterm/xterm';
	import type { AttachAddon as AttachAddonType } from '@xterm/addon-attach';
	import type { FitAddon as FitAddonType } from '@xterm/addon-fit';
	import type { WebglAddon as WebglAddonType } from '@xterm/addon-webgl';
	import { browser } from '$app/environment';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import Copy from 'lucide-svelte/icons/copy';
	import { Button } from 'flowbite-svelte';
	import { toast } from '@zerodevx/svelte-toast';

	let Terminal: typeof TerminalType;
	let AttachAddon: typeof AttachAddonType;
	let FitAddon: typeof FitAddonType;
	let WebglAddon: typeof WebglAddonType;
	onMount(async () => {
		Terminal = (await import('@xterm/xterm')).Terminal;
		AttachAddon = (await import('@xterm/addon-attach')).AttachAddon;
		FitAddon = (await import('@xterm/addon-fit')).FitAddon;
		WebglAddon = (await import('@xterm/addon-webgl')).WebglAddon;
		terminal = new Terminal(options);
		terminal.open(divElement);
		if (browser) {
			window.terminals = window.terminals || [];
			window.terminals.push(terminal);
		}
	});

	interface Props {
		deploymentInfo: DeploymentInfo;
	}

	let { deploymentInfo }: Props = $props();

	let terminal: TerminalType = $state();
	let divElement: HTMLDivElement = $state();
	let ws: WebSocket;

	const options: ITerminalOptions & ITerminalInitOnlyOptions = {
		cursorBlink: true,
		letterSpacing: 0
	};

	const initTerminal = async (deployment_info: DeploymentInfo, terminal: TerminalType) => {
		const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
		const url = `${scheme}://${window.location.host}/api/terminal/${deployment_info.id}`;
		ws = new WebSocket(url);

		const fitAddon = new FitAddon();
		terminal.loadAddon(fitAddon);
		fitAddon.fit();

		const fitTerminal = () => {
			fitAddon?.fit();
			const dims = fitAddon.proposeDimensions();
			if (ws.readyState === ws.OPEN) {
				ws.send(`\x04${JSON.stringify(dims)}`);
			}
		};

		const observer = new ResizeObserver(fitTerminal);
		if (terminal.element) observer.observe(terminal.element);

		const webglAddon = new WebglAddon();
		terminal.loadAddon(webglAddon);

		terminal.writeln(`Connecting...`);
		const attachAddon = new AttachAddon(ws);
		terminal.loadAddon(attachAddon);

		let initialFit = true;
		terminal.onData(() => {
			if (initialFit) {
				fitTerminal();
				initialFit = false;
			}
		});
	};

	const resetConnection = () => {
		terminal?.reset();
		ws?.close();
	};

	onDestroy(() => {
		resetConnection();
		if (browser) {
			window.terminals = window.terminals.filter((t) => t !== terminal);
		}
	});

	let oldDeploymentInfoId: string | undefined = undefined;

	const reInitTerminal = () => {
		// only re-init terminal if deployment id has changed
		if (oldDeploymentInfoId !== deploymentInfo.id) {
			oldDeploymentInfoId = deploymentInfo.id;
			resetConnection();
			initTerminal(deploymentInfo, terminal);
		}
	};

	const getToken = async () => {
		const response = await fetch(`/api/access_client_token/${deploymentInfo.id}`, {
			method: 'POST'
		});
		if (!response.ok) {
			throw new Error('Failed to get token');
		}
		return response.json();
	};

	run(() => {
		if (browser && deploymentInfo.id && terminal) {
			reInitTerminal();
		}
	});
</script>

<div>
	<div class="flex mb-2">
		<Button
			class="ml-auto flex flex-end"
			onclick={async () => {
				// copy "test"
				const token = await getToken();
				console.log('Token:', token);
				const command =
					`ssh -o 'ProxyCommand nix shell github:thymis-io/http-network-relay --command access-client ` +
					`--relay-url ${window.location.protocol == 'https' ? 'wss' : 'ws'}://${window.location.host}/agent/relay_for_clients ` +
					`--secret ${token.token} ${token.deployment_info_id} localhost %p tcp' root@${token.deployment_info_id}.thymis.cloud.internal`;
				await navigator.clipboard.writeText(command);
				toast.push('SSH command copied to clipboard', {
					duration: 2000,
					initial: 1
				});
			}}
		>
			<span>Copy SSH Command </span>
			<Copy class="ml-3" />
		</Button>
	</div>
	<div class="w-full h-full" bind:this={divElement}></div>
</div>
