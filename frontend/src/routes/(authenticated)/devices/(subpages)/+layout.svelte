<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/state';
	import { invalidate } from '$app/navigation';
	import { Modal } from 'flowbite-svelte';
	import Page from '#lib/components/layout/Page.svelte';
	import Tabbar from '#lib/components/Tabbar.svelte';
	import CreateButton from '#lib/components/layout/CreateButton.svelte';
	import PairingCodeDisplay from '#lib/components/PairingCodeDisplay.svelte';
	import { createPairingCode, type PairingCode } from '#lib/pairingCodes.js';
	import Server from 'lucide-svelte/icons/server';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import Archive from 'lucide-svelte/icons/archive';
	import KeyRound from 'lucide-svelte/icons/key-round';

	import type { LayoutData } from './$types';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	const pairingCodesHref = '/devices/pairing-codes';

	let activeCount = $derived(data.globalState.deploymentInfos.filter((di) => !di.archived).length);
	let withoutDeploymentCount = $derived(
		data.hardwareDevices.filter((hd) => !hd.deployment_info_id).length
	);
	let archivedCount = $derived(data.globalState.deploymentInfos.filter((di) => di.archived).length);
	let onPairingCodesTab = $derived(page.url.pathname === pairingCodesHref);

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
		},
		{
			name: $t('hardware-devices.tabs.pairing-codes'),
			href: pairingCodesHref,
			icon: KeyRound,
			count: data.pairingCodes.active.length
		}
	]);

	let createdCode = $state<PairingCode | undefined>();

	const createParingCode = async () => {
		createdCode = await createPairingCode();
		await invalidate('/api/pairing-codes');
	};
</script>

<Page title={$t('nav.devices')} subtitle={$t('hardware-devices.subtitle')}>
	{#snippet actions()}
		{#if onPairingCodesTab}
			<CreateButton label={$t('pairing-codes.create')} onclick={createParingCode} />
		{/if}
	{/snippet}
	<Tabbar items={tabs} />
	{@render children?.()}
</Page>

<Modal
	open={!!createdCode}
	title={$t('pairing-codes.created-title')}
	size="lg"
	outsideclose
	on:close={() => (createdCode = undefined)}
>
	{#if createdCode}
		<PairingCodeDisplay pairingCode={createdCode} />
	{/if}
</Modal>
