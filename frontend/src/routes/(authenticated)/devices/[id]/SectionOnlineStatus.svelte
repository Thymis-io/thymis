<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Badge } from 'flowbite-svelte';
	import Section from './Section.svelte';

	interface Props {
		connectionHistory: Array<{ connected_at: string; disconnected_at?: string }>;
	}
	let { connectionHistory }: Props = $props();

	const isOnline = $derived(connectionHistory.length > 0 && !connectionHistory[0].disconnected_at);

	function formatTime(dateStr: string) {
		return new Date(dateStr).toLocaleString();
	}
</script>

<Section title={$t('device-details.online-status')}>
	<div class="mb-4">
		<Badge color={isOnline ? 'green' : 'red'}>
			{isOnline ? $t('device-details.online') : $t('device-details.offline')}
		</Badge>
	</div>
	<h3 class="mb-2 font-semibold">{$t('device-details.connection-history')}</h3>
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
