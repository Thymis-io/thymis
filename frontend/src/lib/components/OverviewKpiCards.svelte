<script lang="ts">
	import { t } from 'svelte-i18n';
	import MonitorCheck from 'lucide-svelte/icons/monitor-check';
	import MonitorX from 'lucide-svelte/icons/monitor-x';
	import Layers from 'lucide-svelte/icons/layers';
	import History from 'lucide-svelte/icons/history';

	interface Props {
		onlineCount: number;
		offlineCount: number;
		onlineConfigsCount: number;
		totalConfigsCount: number;
		assignedDevices: number;
		behindCount: number;
	}
	let {
		onlineCount,
		offlineCount,
		onlineConfigsCount,
		totalConfigsCount,
		assignedDevices,
		behindCount
	}: Props = $props();
</script>

<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
	<a href="/devices?status=online" class="ds-stat block transition hover:brightness-105">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot online"></span>{$t('overview.kpi.online')}
				</div>
				<div class="ds-stat-value">{onlineCount}</div>
			</div>
			<div class="ds-icon-tile online"><MonitorCheck class="h-[18px] w-[18px]" /></div>
		</div>
	</a>

	<a href="/devices?status=offline" class="ds-stat block transition hover:brightness-105">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot offline"></span>{$t('overview.kpi.offline')}
				</div>
				<div class="ds-stat-value">{offlineCount}</div>
			</div>
			<div class="ds-icon-tile offline"><MonitorX class="h-[18px] w-[18px]" /></div>
		</div>
	</a>

	<div class="ds-stat">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot info"></span>{$t('overview.kpi.config-status')}
				</div>
				<div class="ds-stat-value">
					{onlineConfigsCount}<span class="ds-stat-sub">/{totalConfigsCount}</span>
				</div>
				<div class="ds-stat-sub">{assignedDevices} {$t('overview.kpi.assigned-devices')}</div>
			</div>
			<div class="ds-icon-tile info"><Layers class="h-[18px] w-[18px]" /></div>
		</div>
	</div>

	<a href="#software-versions" class="ds-stat block transition hover:brightness-105">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot {behindCount > 0 ? 'warning' : 'online'}"></span>{$t(
						'overview.kpi.devices-behind'
					)}
				</div>
				<div class="ds-stat-value">{behindCount}</div>
				{#if behindCount === 0}
					<div class="ds-stat-sub">{$t('overview.kpi.all-up-to-date')}</div>
				{/if}
			</div>
			<div class="ds-icon-tile {behindCount > 0 ? 'warning' : 'online'}">
				<History class="h-[18px] w-[18px]" />
			</div>
		</div>
	</a>
</div>
