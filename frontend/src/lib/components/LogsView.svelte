<script lang="ts">
	import { t } from 'svelte-i18n';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import type { LogLine } from '$lib/logs';
	import type { GlobalState } from '$lib/state.svelte';
	import { queryParameters } from 'sveltekit-search-params';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { Toggle, Dropdown as FlowbiteDropdown, DropdownItem } from 'flowbite-svelte';
	import AutoComplete from '$lib/components/AutoComplete.svelte';
	import { calcTimeSince } from '$lib/hardwareDevices';
	import { onMount } from 'svelte';

	interface Props {
		globalState: GlobalState;
		logs: LogLine[];
		programNames: string[] | undefined;
		deploymentInfos: DeploymentInfo[];
		connectedDeploymentInfos: DeploymentInfo[];
		selectedDeploymentInfoId: string | null | undefined;
		/** Show the device selector dropdown (multi-device contexts). */
		showSelector?: boolean;
		/** Called when the device selector changes (only used when showSelector). */
		onSelectDeploymentInfo?: (id: string) => void;
	}

	let {
		globalState,
		logs,
		programNames,
		deploymentInfos,
		connectedDeploymentInfos,
		selectedDeploymentInfoId,
		showSelector = false,
		onSelectDeploymentInfo
	}: Props = $props();

	let downloadOpen = $state(false);
	let refreshInterval = $state(5000);

	const refreshIntervals = [
		{ label: $t('logs.refresh_off'), value: 0 },
		{ label: $t('logs.refresh_1s'), value: 1000 },
		{ label: $t('logs.refresh_5s'), value: 5000 },
		{ label: $t('logs.refresh_10s'), value: 10000 },
		{ label: $t('logs.refresh_30s'), value: 30000 },
		{ label: $t('logs.refresh_60s'), value: 60000 }
	];

	const downloadOptions = [
		{ minutes: 5, label: $t('logs.download-5min') },
		{ minutes: 15, label: $t('logs.download-15min') },
		{ minutes: 60, label: $t('logs.download-1hr') },
		{ minutes: 60 * 6, label: $t('logs.download-6hr') },
		{ minutes: 60 * 24, label: $t('logs.download-1day') },
		{ minutes: 60 * 24 * 7, label: $t('logs.download-7day') },
		{ minutes: 60 * 24 * 14, label: $t('logs.download-14day') }
	];

	const onlineThresholdMs = 30000;
	const deploymentInfoRefreshMs = 10000;

	const sortedDeploymentInfos = $derived(
		deploymentInfos.toSorted(
			(a, b) =>
				(b.last_seen ? new Date(b.last_seen).getTime() : -1000) -
				(a.last_seen ? new Date(a.last_seen).getTime() : -1000)
		)
	);

	const params = queryParameters();

	const getLabel = (info: DeploymentInfo) => {
		const displayName = globalState.config(info.deployed_config_id)?.displayName;
		const online =
			info.last_seen && new Date(info.last_seen) > new Date(Date.now() - onlineThresholdMs);
		const lastSeen = info.last_seen
			? calcTimeSince(new Date(info.last_seen), new Date())
			: $t('configurations.status.never-seen');
		return `${info.name || info.id} (${online ? $t('configurations.status.online') : lastSeen})`;
	};

	const getDownloadUrl = (deploymentId: string | null | undefined, minutes: number) => {
		return `/api/logs/${deploymentId}/download?duration_minutes=${minutes}`;
	};

	$effect(() => {
		if (refreshInterval <= 0) return;

		const interval = setInterval(async () => {
			if (!connectedDeploymentInfos.find((info) => info.id === selectedDeploymentInfoId)) {
				return;
			}

			await invalidateButDeferUntilNavigation((url) =>
				url.pathname.startsWith(`/api/logs/${selectedDeploymentInfoId}`)
			);
		}, refreshInterval);

		return () => clearInterval(interval);
	});

	onMount(() => {
		const interval = setInterval(async () => {
			await invalidateButDeferUntilNavigation(
				(url) =>
					url.pathname.startsWith('/api/deployment_info') ||
					url.pathname.startsWith('/api/all_deployment_info')
			);
		}, deploymentInfoRefreshMs);

		return () => clearInterval(interval);
	});
</script>

<div class="mb-4 flex flex-wrap items-center gap-4">
	{#if showSelector}
		<Dropdown
			selected={selectedDeploymentInfoId}
			values={sortedDeploymentInfos.map((info) => ({
				label: getLabel(info),
				value: info.id
			}))}
			onSelected={(value) => {
				onSelectDeploymentInfo?.(value);
				return value;
			}}
			class="w-120 min-w-60"
			innerClass="px-2"
		/>
	{/if}
	<Dropdown
		values={refreshIntervals}
		selected={refreshInterval}
		onSelected={(value) => (refreshInterval = value)}
		class="whitespace-nowrap"
		innerClass="px-2"
	/>
	<AutoComplete
		placeholder={$t('logs.filter-by-program-name')}
		options={programNames?.map((name) => ({ label: name, value: name }))}
		allowCustomValues={true}
		value={params['program-name'] ?? ''}
		onChange={(value) => {
			params['program-name'] = value.trim() === '' ? null : value;
		}}
		class="w-96"
	/>
	<!-- exact program name -->
	<span>{$t('logs.exact-program-name')}</span>
	<Toggle
		checked={params['exact-program-name'] === 'true'}
		on:change={(e) => {
			params['exact-program-name'] = (e.target as HTMLInputElement).checked.toString();
		}}
	/>
	<button class="ds-btn">
		{$t('logs.download')}
		<ChevronDown class="h-4 w-4 ml-1" />
	</button>
	<FlowbiteDropdown bind:open={downloadOpen}>
		{#each downloadOptions as { minutes, label }}
			<DropdownItem
				href={getDownloadUrl(selectedDeploymentInfoId, minutes)}
				download
				on:click={() => (downloadOpen = false)}
			>
				{label}
			</DropdownItem>
		{/each}
	</FlowbiteDropdown>
</div>
<div class="ds-card ds-card-pad w-full overflow-x-auto" style="color: var(--ds-text)">
	{#if logs.length === 0}
		<p class="italic" style="color: var(--ds-text-mute)">{$t('logs.no-logs')}</p>
	{/if}
	{#each logs.toReversed() as line (line.uuid)}
		<p class="whitespace-pre font-mono text-[12.5px] leading-relaxed">
			{`${new Date(line.timestamp).toUTCString()} ${line.programname}: ${line.message}`}
		</p>
	{/each}
</div>
