<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { ConnectionHistoryEntry } from '$lib/deploymentInfo';

	interface Props {
		connectionHistory: ConnectionHistoryEntry[];
	}
	let { connectionHistory }: Props = $props();

	function formatTime(dateStr: string) {
		return new Date(dateStr).toLocaleString();
	}
</script>

<Section title={$t('device-details.connection-history')}>
	<div class="space-y-2">
		{#each connectionHistory as conn}
			<div class="border-l-4 border-blue-500 py-2 pl-3">
				<p class="text-sm">
					<strong>{$t('device-details.connected')}:</strong>
					{formatTime(conn.connected_at)}
				</p>
				{#if conn.disconnected_at}
					<p class="text-sm">
						<strong>{$t('device-details.disconnected')}:</strong>
						{formatTime(conn.disconnected_at)}
					</p>
				{/if}
			</div>
		{/each}
	</div>
</Section>
