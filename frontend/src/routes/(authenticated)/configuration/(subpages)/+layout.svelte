<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState } from '$lib/state';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import Download from 'lucide-svelte/icons/download';
	import Play from 'lucide-svelte/icons/play';
	import { type Config } from '$lib/state';
	import { getConfigImageFormat } from '$lib/config/configUtils';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { Button } from 'flowbite-svelte';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidate } from '$app/navigation';
	import type { LayoutData } from './$types';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let openCommitModal = $state(false);

	let isVM = $derived(getConfigImageFormat(data.nav.selectedConfig) == 'nixos-vm');
	let selectedTargetName = $derived(data.nav.selectedTarget?.displayName ?? '');
	let title = $derived.by(() => {
		if (data.nav.selectedTargetType === 'config') {
			return `${$t('configurations.details-title')}: ${selectedTargetName}`;
		}
		if (data.nav.selectedTargetType === 'tag') {
			return `${$t('tags.details-title')}: ${selectedTargetName}`;
		}
		return selectedTargetName;
	});

	const commit = async (message: string) => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidate(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);
	};

	const buildAndDownloadImage = async (config: Config | undefined) => {
		if (!config) return;
		await saveState(data.globalState);
		await fetchWithNotify(`/api/action/build-download-image?identifier=${config.identifier}`, {
			method: 'POST'
		});
	};
</script>

<CommitModal
	bind:open={openCommitModal}
	repoStatus={data.repoStatus}
	title={isVM
		? $t('configurations.actions.build-vm-and-start')
		: $t('configurations.actions.download')}
	defaultMessage={isVM
		? $t('taskbar.task-types.run_nixos_vm_task', { values: { device: selectedTargetName } })
		: $t('taskbar.task-types.build_device_image', { values: { device: selectedTargetName } })}
	action={isVM
		? $t('configurations.actions.commit-build-vm-and-start')
		: $t('configurations.actions.commit-download')}
	onAction={async (message) => {
		openCommitModal = false;
		await commit(message);
		await buildAndDownloadImage(data.nav.selectedConfig);
	}}
/>
<PageHead {title} repoStatus={data.repoStatus} globalState={data.globalState} nav={data.nav}>
	{#if data.nav.selectedConfig}
		<Button
			color="alternative"
			class="whitespace-nowrap gap-2 px-2 py-1 m-1"
			on:click={async () => {
				await saveState(data.globalState);
				await invalidate((url) => url.pathname === '/api/repo_status');

				if (data.repoStatus.changes.length > 0) {
					openCommitModal = true;
				} else {
					await buildAndDownloadImage(data.nav.selectedConfig);
				}
			}}
		>
			{#if isVM}
				<Play size={'1rem'} class="min-w-4" />
				<span class="text-base whitespace-nowrap">
					{$t('configurations.actions.build-vm-and-start')}
				</span>
			{:else}
				<Download size={'1rem'} class="min-w-4" />
				<span class="text-base whitespace-nowrap">{$t('configurations.actions.download')}</span>
			{/if}
		</Button>
	{/if}
</PageHead>
<Tabbar globalState={data.globalState} nav={data.nav} />
{@render children?.()}
