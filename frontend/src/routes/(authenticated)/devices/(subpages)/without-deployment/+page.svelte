<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import { getHardwareKeyDisplayName } from '$lib/hardwareDevices';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let hardwareDevicesWithoutDeployment = $derived(
		data.hardwareDevices.filter((hd) => !hd.deployment_info_id)
	);
</script>

<DataTable
	columns={[
		{ label: $t('hardware-devices.table.hardware-ids') },
		{ label: $t('hardware-devices.table.last-seen') }
	]}
	rows={hardwareDevicesWithoutDeployment}
	empty={$t('hardware-devices.no-known-hardware-devices-without-known-deployment')}
>
	{#snippet row(hardwareDevice)}
		<td>
			{#each Object.entries(hardwareDevice.hardware_ids) as [hardwareIdKey, hardwareValue]}
				<div class="ds-mono">
					{getHardwareKeyDisplayName(hardwareIdKey)}: {hardwareValue}
				</div>
			{/each}
		</td>
		<td>
			<RenderTimeAgo timestamp={hardwareDevice.last_seen} />
		</td>
	{/snippet}
</DataTable>
