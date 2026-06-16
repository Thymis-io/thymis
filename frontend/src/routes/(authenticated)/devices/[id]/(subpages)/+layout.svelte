<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Modal } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import ListCollapse from 'lucide-svelte/icons/list-collapse';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TerminalIcon from 'lucide-svelte/icons/terminal';
	import FileText from 'lucide-svelte/icons/file-text';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { updateDeploymentInfo, isOnline as checkOnline } from '$lib/deploymentInfo';
	import { invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import type { LayoutData } from './$types';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let deploymentInfo = $derived(data.deploymentInfo);
	let config = $derived(
		data.globalState.configs.find((c) => c.identifier === deploymentInfo.deployed_config_id)
	);
	let isOnline = $derived(checkOnline(deploymentInfo.last_seen));
	let hasVnc = $derived(!!config && targetShouldShowVNC(config, data.globalState));

	// Tab definitions — VNC is gated on the deployed config exposing a VNC module.
	let deviceTabs = $derived([
		{
			id: 'details',
			href: `/devices/${deploymentInfo.id}/details`,
			icon: ListCollapse,
			labelKey: 'nav.device-details'
		},
		...(hasVnc
			? [
					{
						id: 'vnc',
						href: `/devices/${deploymentInfo.id}/vnc`,
						icon: ScreenShare,
						labelKey: 'nav.device-vnc'
					}
				]
			: []),
		{
			id: 'terminal',
			href: `/devices/${deploymentInfo.id}/terminal`,
			icon: TerminalIcon,
			labelKey: 'nav.terminal'
		},
		{ id: 'logs', href: `/devices/${deploymentInfo.id}/logs`, icon: FileText, labelKey: 'nav.logs' }
	]);

	let nameModalOpen = $state(false);
	let nameInput = $state('');

	function openNameModal() {
		nameInput = deploymentInfo.name ?? '';
		nameModalOpen = true;
	}

	async function saveName() {
		const response = await updateDeploymentInfo(fetch, deploymentInfo.id, {
			name: nameInput || null
		});
		if (response.ok) {
			nameModalOpen = false;
			await invalidate(`/api/deployment_info/${deploymentInfo.id}`);
		}
	}

	const restartDevice = async () => {
		if (!config) return;
		await fetchWithNotify(`/api/action/restart-device?identifier=${config.identifier}`, {
			method: 'POST'
		});
	};
</script>

<PageHead
	title={deploymentInfo.name ?? deploymentInfo.id}
	subtitle={deploymentInfo.reachable_deployed_host ?? undefined}
	selectedDeploymentInfo={deploymentInfo}
>
	<button
		onclick={openNameModal}
		class="rounded p-1"
		style="color: var(--ds-text-mute)"
		title={$t('device-details.edit')}
	>
		<Pen class="h-[18px] w-[18px]" />
	</button>
	<span class="ds-status-pill {isOnline ? 'online' : 'offline'}">
		<span class="ds-dot"></span>
		{isOnline ? $t('device-details.online') : $t('device-details.offline')}
	</span>

	{#snippet actions()}
		{#if config}
			<button class="ds-btn" onclick={restartDevice}>
				<RotateCcw size={'1rem'} class="min-w-4" />
				<span class="whitespace-nowrap">{$t('configurations.actions.restart')}</span>
			</button>
		{/if}
	{/snippet}
</PageHead>

<Modal bind:open={nameModalOpen} title={$t('device-details.edit')}>
	<Input bind:value={nameInput} placeholder={$t('device-details.name-placeholder')} />
	<p class="mt-2 text-xs" style="color: var(--ds-text-mute)">{$t('device-details.name-helper')}</p>
	<div class="mt-4 flex justify-end gap-2">
		<button class="ds-btn" onclick={() => (nameModalOpen = false)}>{$t('common.cancel')}</button>
		<button class="ds-btn ds-btn-primary" onclick={saveName}>{$t('device-details.save')}</button>
	</div>
</Modal>

<div class="mb-4 flex flex-wrap gap-1 border-b border-[var(--ds-border)]" role="tablist">
	{#each deviceTabs as tab (tab.id)}
		{@const isSelected = page.url.pathname === tab.href}
		<a
			role="tab"
			aria-selected={page.url.pathname === tab.href}
			href={tab.href}
			class="-mb-px border-b-2 p-2 px-3 text-center text-sm font-medium {isSelected
				? 'border-[var(--ds-accent)] text-[var(--ds-accent-strong)]'
				: 'border-transparent text-[var(--ds-text-dim)] hover:text-[var(--ds-text)]'}"
		>
			<div class="flex items-center gap-2 px-1 font-semibold md:min-w-32 xl:min-w-48">
				<tab.icon size={18} />
				<span>{$t(tab.labelKey)}</span>
			</div>
		</a>
	{/each}
</div>

{@render children?.()}
