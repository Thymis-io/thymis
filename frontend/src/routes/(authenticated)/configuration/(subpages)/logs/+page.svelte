<script lang="ts">
	import { t } from 'svelte-i18n';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { queryParameters } from 'sveltekit-search-params';
	import type { PageData } from './$types';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import {
		Button,
		Card,
		Toggle,
		Dropdown as FlowbiteDropdown,
		DropdownItem
	} from 'flowbite-svelte';
	import AutoComplete from '$lib/components/AutoComplete.svelte';
	import { calcTimeSince } from '$lib/hardwareDevices';
	import { onMount } from 'svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let downloadOpen = $state(false);
	let refreshInterval = $state(1000);

	const refreshIntervals = [
		{ label: 'Off', value: 0 },
		{ label: '1s', value: 1000 },
		{ label: '5s', value: 5000 },
		{ label: '10s', value: 10000 },
		{ label: '60s', value: 60000 }
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

	const deploymentInfos = $derived(
		data.deploymentInfos.toSorted(
			(a, b) =>
				(b.last_seen ? new Date(b.last_seen).getTime() : -1000) -
				(a.last_seen ? new Date(a.last_seen).getTime() : -1000)
		)
	);

	const params = queryParameters();
	let selectedDeploymentInfoId = $derived.by(() => params['deployment-info-id']);

	const getLabel = (info: DeploymentInfo) => {
		const displayName = data.globalState.config(info.deployed_config_id)?.displayName;
		const online =
			info.last_seen && new Date(info.last_seen) > new Date(Date.now() - onlineThresholdMs);
		const lastSeen = info.last_seen
			? calcTimeSince(new Date(info.last_seen), new Date())
			: $t('configurations.status.never-seen');
		return `${displayName ?? info.deployed_config_id} (${online ? $t('configurations.status.online') : lastSeen})`;
	};

	const getDownloadUrl = (deploymentId: string | null, minutes: number) => {
		return `/api/logs/${deploymentId}/download?duration_minutes=${minutes}`;
	};

	$effect(() => {
		if (refreshInterval <= 0) return;

		const interval = setInterval(async () => {
			if (!data.connectedDeploymentInfos.find((info) => info.id === selectedDeploymentInfoId)) {
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

<div class="mb-4 flex items-center gap-4">
	<Dropdown
		selected={selectedDeploymentInfoId}
		values={deploymentInfos.map((info) => ({
			label: getLabel(info),
			value: info.id
		}))}
		onSelected={(value) => (params['deployment-info-id'] = value)}
		class="w-120"
		innerClass="px-2"
	/>
	<Dropdown
		values={refreshIntervals}
		selected={refreshInterval}
		onSelected={(value) => (refreshInterval = value)}
		class="w-20"
		innerClass="px-2"
	/>
	<AutoComplete
		placeholder={$t('logs.filter-by-program-name')}
		options={data.programNames?.map((name) => ({ label: name, value: name }))}
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
	<Button>
		{$t('logs.download')}
		<ChevronDown class="h-4 w-4 ml-1" />
	</Button>
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
<Card class="w-full max-w-full overflow-x-auto">
	{#each data.logs.toReversed() as line (line.uuid)}
		<p class="font-mono whitespace-pre">
			{`${new Date(line.timestamp).toUTCString()} ${line.programname}: ${line.message}`}
		</p>
	{/each}
</Card>
