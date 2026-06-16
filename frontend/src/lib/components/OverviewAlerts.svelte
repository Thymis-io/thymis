<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetAlert } from '$lib/fleet';
	import TriangleAlert from 'lucide-svelte/icons/triangle-alert';
	import CircleCheck from 'lucide-svelte/icons/check-circle';

	interface Props {
		alerts: FleetAlert[];
	}
	let { alerts }: Props = $props();

	const severityColor: Record<FleetAlert['severity'], string> = {
		critical: '#ef4444',
		warning: '#f59e0b'
	};
</script>

<div class="ds-card-pad">
	{#if !alerts.length}
		<div class="flex items-center gap-2 py-6 text-sm" style="color: var(--ds-text-dim)">
			<CircleCheck class="h-5 w-5" style="color: #10b981" />
			{$t('overview.alerts.none')}
		</div>
	{:else}
		<div class="space-y-1.5">
			{#each alerts as alert (alert.deployment_info_id + ':' + alert.kind)}
				<a
					href={`/devices/${alert.deployment_info_id}`}
					class="flex items-center gap-3 rounded px-2 py-1.5"
					style="background: var(--ds-surface-2, transparent)"
				>
					<TriangleAlert class="h-4 w-4 shrink-0" style="color: {severityColor[alert.severity]}" />
					<span class="truncate text-sm" style="color: var(--ds-text)">
						{alert.name ?? alert.deployment_info_id.slice(0, 8)}
					</span>
					<span class="ml-auto truncate text-xs" style="color: var(--ds-text-dim)">
						{alert.detail}
					</span>
				</a>
			{/each}
		</div>
	{/if}
</div>
