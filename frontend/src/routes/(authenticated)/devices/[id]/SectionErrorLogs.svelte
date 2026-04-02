<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';

	interface Props {
		errorLogs: Array<{
			timestamp: string;
			message: string;
			severity: number;
			syslogtag: string;
		}>;
	}
	let { errorLogs }: Props = $props();

	const severityLabel: Record<number, string> = {
		0: 'Emergency',
		1: 'Alert',
		2: 'Critical',
		3: 'Error'
	};
</script>

<Section title={$t('device-details.error-logs')}>
	{#if !errorLogs.length}
		<p class="text-gray-500">{$t('device-details.no-error-logs')}</p>
	{:else}
		<div class="space-y-2">
			{#each errorLogs as log}
				<div class="rounded border border-red-200 bg-red-50 p-3">
					<div class="flex items-center justify-between">
						<span class="text-xs font-semibold text-red-700">
							{severityLabel[log.severity] ?? 'Error'}
						</span>
						<span class="text-xs text-gray-500">
							{new Date(log.timestamp).toLocaleString()}
						</span>
					</div>
					<p class="mt-1 font-mono text-sm">{log.syslogtag}: {log.message}</p>
				</div>
			{/each}
		</div>
	{/if}
</Section>
