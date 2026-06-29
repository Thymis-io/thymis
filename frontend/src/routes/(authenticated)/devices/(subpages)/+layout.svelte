<script lang="ts">
	import { t } from 'svelte-i18n';
	import Page from '$lib/components/layout/Page.svelte';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import Server from 'lucide-svelte/icons/server';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import Archive from 'lucide-svelte/icons/archive';

	import type { LayoutData } from './$types';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let activeCount = $derived(data.globalState.deploymentInfos.filter((di) => !di.archived).length);
	let withoutDeploymentCount = $derived(
		data.hardwareDevices.filter((hd) => !hd.deployment_info_id).length
	);
	let archivedCount = $derived(data.globalState.deploymentInfos.filter((di) => di.archived).length);

	let tabs = $derived([
		{
			name: $t('hardware-devices.tabs.active'),
			href: '/devices/active',
			icon: Server,
			count: activeCount
		},
		{
			name: $t('hardware-devices.tabs.without-deployment'),
			href: '/devices/without-deployment',
			icon: HardDrive,
			count: withoutDeploymentCount
		},
		{
			name: $t('hardware-devices.tabs.archived'),
			href: '/devices/archived',
			icon: Archive,
			count: archivedCount
		}
	]);
</script>

<Page title={$t('nav.devices')} subtitle={$t('hardware-devices.subtitle')}>
	<Tabbar items={tabs} />
	{@render children?.()}
</Page>
