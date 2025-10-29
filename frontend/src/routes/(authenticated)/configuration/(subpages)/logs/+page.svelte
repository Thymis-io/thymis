<script lang="ts">
	import { t } from 'svelte-i18n';
	import Dropdown from '$lib/components/Dropdown.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { queryParameters } from 'sveltekit-search-params';
	import type { PageData } from './$types';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import { Card, Toggle } from 'flowbite-svelte';
	import AutoComplete from '$lib/components/AutoComplete.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let refreshInterval = $state(1000);

	const deploymentInfos = $derived(
		data.deploymentInfos.toSorted(
			(a, b) => new Date(b.last_seen).getDate() - new Date(a.last_seen).getDate()
		)
	);

	const params = queryParameters();
	let selectedDeploymentInfoId = $derived.by(() => {
		const id = params['deployment-info-id'];
		if (!deploymentInfos.find((info) => info.id === id)) {
			return deploymentInfos.length > 0 ? deploymentInfos[0].id : null;
		} else {
			return id;
		}
	});

	const getLabel = (info: DeploymentInfo) => {
		const displayName = data.globalState.config(info.deployed_config_id)?.displayName;
		const lastSeen = new Date(info.last_seen).toUTCString();
		return `${displayName ?? info.deployed_config_id} - ${lastSeen}`;
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
		values={[
			{ label: 'Off', value: 0 },
			{ label: '1s', value: 1000 },
			{ label: '5s', value: 5000 },
			{ label: '10s', value: 10000 }
		]}
		selected={refreshInterval}
		onSelected={(value) => (refreshInterval = value)}
		class="w-32"
		innerClass="px-2"
	/>
	<AutoComplete
		placeholder={$t('logs.filter-by-program-name')}
		options={data.programNames?.map((name) => ({ label: name, value: name }))}
		allowCustomValues={true}
		value={params['program-name'] ?? ''}
		onChange={(value) => {
			if (value.trim() === '') {
				params['program-name'] = null;
			} else {
				params['program-name'] = value;
			}
		}}
		class="w-96"
	/>
	<!-- exact program name -->
	<span>{$t('logs.exact-program-name')}</span>
	<Toggle
		checked={params['exact-program-name'] === 'true'}
		on:change={(e) =>
			(params['exact-program-name'] = (e.target as HTMLInputElement).checked.toString())}
	/>
</div>
<Card class="w-full max-w-full overflow-x-auto">
	{#each data.logs.toReversed() as line (line.id)}
		<p class="font-mono whitespace-pre">
			{`${new Date(line.timestamp).toUTCString()} ${line.programname}: ${line.message}`}
		</p>
	{/each}
</Card>
