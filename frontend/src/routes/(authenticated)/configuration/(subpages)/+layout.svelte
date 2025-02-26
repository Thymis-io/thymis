<script lang="ts">
	import { t } from 'svelte-i18n';
	import { globalNavSelectedTargetType, globalNavSelectedTarget, saveState } from '$lib/state';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import PageHead from '$lib/components/PageHead.svelte';
	import Download from 'lucide-svelte/icons/download';
	import Play from 'lucide-svelte/icons/play';
	import { globalNavSelectedConfig, type Config } from '$lib/state';
	import { getConfigImageFormat } from '$lib/config/configUtils';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { Button } from 'flowbite-svelte';
	import type { LayoutData } from './$types';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidate } from '$app/navigation';

	export let data: LayoutData;

	let openCommitModal = false;

	$: isVM = getConfigImageFormat($globalNavSelectedConfig) == 'nixos-vm';
	$: selectedTargetName = $globalNavSelectedTarget?.displayName ?? '';
	$: titleMap = {
		config: `${$t('configurations.details-title')}: ${selectedTargetName}`,
		tag: `${$t('tags.details-title')}: ${selectedTargetName}`,
		null: selectedTargetName
	};
	$: title = titleMap[$globalNavSelectedTargetType ?? 'null'];

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
		await saveState();
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
	onAction={(message) => {
		openCommitModal = false;
		commit(message);
		buildAndDownloadImage($globalNavSelectedConfig);
	}}
/>
<PageHead {title} repoStatus={data.repoStatus}>
	{#if $globalNavSelectedConfig}
		<Button
			color="alternative"
			class="whitespace-nowrap gap-2 px-2 py-1 m-1"
			on:click={() => {
				if (data.repoStatus.changes.length > 0) {
					openCommitModal = true;
				} else {
					buildAndDownloadImage($globalNavSelectedConfig);
				}
			}}
		>
			{#if isVM}
				<Play size={'1rem'} class="min-w-4" />
				<span class="text-base whitespace-nowrap"
					>{$t('configurations.actions.build-vm-and-start')}</span
				>
			{:else}
				<Download size={'1rem'} class="min-w-4" />
				<span class="text-base whitespace-nowrap">{$t('configurations.actions.download')}</span>
			{/if}
		</Button>
	{/if}
</PageHead>
<Tabbar />
<slot />
