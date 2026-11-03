<script lang="ts">
	import { t } from 'svelte-i18n';
	import MonitorCheck from 'lucide-svelte/icons/monitor-check';
	import MonitorX from 'lucide-svelte/icons/monitor-x';
	import Layers from 'lucide-svelte/icons/layers';
	import History from 'lucide-svelte/icons/history';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';

	interface Props {
		onlineCount: number;
		offlineCount: number;
		onlineConfigsCount: number;
		totalConfigsCount: number;
		behindCount: number;
		rebootRequiredCount: number;
	}
	let {
		onlineCount,
		offlineCount,
		onlineConfigsCount,
		totalConfigsCount,
		behindCount,
		rebootRequiredCount
	}: Props = $props();
</script>

<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
	<a href="/devices/active?status=online" class="ds-stat block transition hover:brightness-105">
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

	<a href="/devices/active?status=offline" class="ds-stat block transition hover:brightness-105">
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

	<a href="#configurations" class="ds-stat block transition hover:brightness-105">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot info"></span>{$t('overview.kpi.config-status')}
				</div>
				<div class="ds-stat-value">
					{onlineConfigsCount}<span class="ds-stat-sub">/{totalConfigsCount}</span>
				</div>
			</div>
			<div class="ds-icon-tile info"><Layers class="h-[18px] w-[18px]" /></div>
		</div>
	</a>

	<a href="#software-versions" class="ds-stat block transition hover:brightness-105">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot {behindCount > 0 ? 'warning' : 'online'}"></span>{$t(
						'overview.kpi.devices-behind'
					)}
				</div>
				<div class="ds-stat-value">{behindCount}</div>
			</div>
			<div class="ds-icon-tile {behindCount > 0 ? 'warning' : 'online'}">
				<History class="h-[18px] w-[18px]" />
			</div>
		</div>
	</a>

	<a
		href="/devices/active?status=reboot-required"
		class="ds-stat block transition hover:brightness-105"
	>
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot {rebootRequiredCount > 0 ? 'warning' : 'online'}"></span>{$t(
						'overview.kpi.reboot-required'
					)}
				</div>
				<div class="ds-stat-value">{rebootRequiredCount}</div>
			</div>
			<div class="ds-icon-tile {rebootRequiredCount > 0 ? 'warning' : 'online'}">
				<RotateCcw class="h-[18px] w-[18px]" />
			</div>
		</div>
	</a>
</div>
