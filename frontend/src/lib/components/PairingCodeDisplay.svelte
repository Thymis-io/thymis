<script lang="ts">
	import { t } from 'svelte-i18n';
	import { toast } from '@zerodevx/svelte-toast';
	import Copy from 'lucide-svelte/icons/copy';
	import type { PairingCode } from '#lib/pairingCodes.js';

	interface Props {
		pairingCode: PairingCode;
		/** `CONTROLLER_HOST` for the agent. */
		controllerUrl: string;
	}

	let { pairingCode, controllerUrl }: Props = $props();

	const methods = ['Python', 'Nix', 'Docker ARM', 'Docker x86'] as const;
	let method = $state<(typeof methods)[number]>('Python');

	let commands = $derived.by(() => {
		const host = controllerUrl;
		const args = `--pairing-code ${pairingCode.code}`;
		const docker = (tag: string) =>
			[
				'docker run -d --name thymis-agent --restart unless-stopped --network host',
				`  -e CONTROLLER_HOST=${host}`,
				'  -v /etc/thymis:/etc/thymis -v /etc/ssh:/etc/ssh:ro -v /root/.ssh:/root/.ssh',
				`  ghcr.io/thymis-io/thymis-agent:${tag} ${args}`
			].join(' \\\n');
		return {
			Python: `CONTROLLER_HOST=${host} uvx --from "git+https://github.com/thymis-io/thymis.git#subdirectory=agent" thymis-agent ${args}`,
			Nix: `CONTROLLER_HOST=${host} nix run github:thymis-io/thymis#thymis-agent -- ${args}`,
			'Docker x86': docker('latest'),
			'Docker ARM': docker('latest-arm64')
		};
	});
	let command = $derived(commands[method]);

	const copy = async (text: string) => {
		await navigator.clipboard.writeText(text);
		toast.push($t('pairing-codes.copied'), { duration: 2000, initial: 1 });
	};
</script>

<div class="flex flex-col gap-8">
	<p class="text-base">{$t('pairing-codes.external-only')}</p>

	<section class="flex flex-col gap-2">
		<h3 class="text-sm font-medium">{$t('pairing-codes.code-label')}</h3>
		<div class="code-box flex items-center justify-between gap-4 px-3 py-2">
			<span
				class="playwright-snapshot-unstable text-base tracking-widest"
				style="font-family: var(--ds-mono)"
				data-testid="pairing-code">{pairingCode.code}</span
			>
			<button class="ds-btn ds-btn-sm" onclick={() => copy(pairingCode.code)}>
				<Copy size={15} />
				{$t('pairing-codes.copy-code')}
			</button>
		</div>
		<p class="playwright-snapshot-unstable text-base">
			{$t('pairing-codes.expires-at', {
				values: { date: new Date(pairingCode.expires_at).toLocaleString() }
			})}
		</p>
	</section>

	<section class="flex flex-col gap-2">
		<h3 class="text-sm font-medium">{$t('pairing-codes.command-label')}</h3>
		<div class="method-tabs" role="tablist">
			{#each methods as m}
				<button
					type="button"
					role="tab"
					aria-selected={method === m}
					class="method-tab"
					class:active={method === m}
					onclick={() => (method = m)}>{m}</button
				>
			{/each}
		</div>
		<div class="code-box flex items-start gap-3 py-3 pl-4 pr-2">
			<pre
				class="playwright-snapshot-unstable min-w-0 flex-1 whitespace-pre-wrap break-all text-base leading-relaxed"
				style="font-family: var(--ds-mono)"><span class="select-none opacity-50"
					>$ </span>{command}</pre>
			<button
				class="ds-icon-btn shrink-0"
				title={$t('pairing-codes.copy-command')}
				aria-label={$t('pairing-codes.copy-command')}
				onclick={() => copy(command)}
			>
				<Copy size={15} />
			</button>
		</div>
		<p class="text-sm" style="color: var(--ds-text-dim)">
			{$t('pairing-codes.run-as-root')}
			<a
				class="underline"
				href="https://thymis.io/docs/device-lifecycle/external-devices"
				target="_blank"
				rel="noopener">{$t('pairing-codes.docs-link')}</a
			>
		</p>
	</section>
</div>

<style>
	.code-box {
		background: var(--ds-surface-2);
		border: 1px solid var(--ds-border);
		border-radius: var(--ds-radius);
	}
	.method-tabs {
		display: flex;
		gap: 1px;
		border-bottom: 1px solid var(--ds-border);
	}
	.method-tab {
		padding: 6px 12px;
		margin-bottom: -1px;
		border-bottom: 2px solid transparent;
		font-size: 13px;
		font-weight: 600;
		color: var(--ds-text-dim);
	}
	.method-tab:hover {
		color: var(--ds-text);
	}
	.method-tab.active {
		color: var(--ds-accent-strong);
		border-bottom-color: var(--ds-accent);
	}
</style>
