<script lang="ts">
	import { t } from 'svelte-i18n';
	import { toast } from '@zerodevx/svelte-toast';
	import Copy from 'lucide-svelte/icons/copy';
	import type { PairingCode } from '#lib/pairingCodes.js';

	interface Props {
		pairingCode: PairingCode;
	}

	let { pairingCode }: Props = $props();

	let command = $derived(
		`CONTROLLER_HOST=${window.location.origin} thymis-agent --pairing-code ${pairingCode.code}`
	);

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
	</section>
</div>

<style>
	.code-box {
		background: var(--ds-surface-2);
		border: 1px solid var(--ds-border);
		border-radius: var(--ds-radius);
	}
</style>
