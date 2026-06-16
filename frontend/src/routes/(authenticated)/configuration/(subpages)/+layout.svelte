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
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import type { LayoutData } from './$types';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import { Modal, Button } from 'flowbite-svelte';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let openCommitModal = $state(false);

	// Rename the selected config/tag via a modal opened from the detail header.
	let renameOpen = $state(false);
	let nameInput = $state('');

	const beginEditName = () => {
		nameInput = data.globalState.selectedTarget?.displayName ?? '';
		renameOpen = true;
	};

	const commitName = async () => {
		const target = data.globalState.selectedTarget;
		const name = nameInput.trim();
		if (target && name && name !== target.displayName) {
			target.displayName = name;
			await saveState(data.globalState);
		}
		renameOpen = false;
	};

	const focusSelect = (node: HTMLInputElement) => {
		setTimeout(() => {
			node.focus();
			node.select();
		}, 50);
	};

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
		await invalidateButDeferUntilNavigation(
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
<Modal bind:open={renameOpen} title={$t('common.rename')} outsideclose size="sm">
	<div class="space-y-2">
		<label class="ds-form-label" for="renameTargetName">{$t('common.name')}</label>
		<input
			id="renameTargetName"
			class="ds-input"
			bind:value={nameInput}
			use:focusSelect
			onkeydown={(e) => {
				if (e.key === 'Enter') commitName();
			}}
		/>
	</div>
	<svelte:fragment slot="footer">
		<Button color="alternative" on:click={() => (renameOpen = false)}>{$t('common.cancel')}</Button>
		<Button on:click={commitName} disabled={!nameInput.trim()}>{$t('common.save')}</Button>
	</svelte:fragment>
</Modal>
<PageHead>
	<h1 class="ds-page-title flex items-center gap-2">
		<IdentifierLink
			identifier={data.globalState.selectedTargetIdentifier}
			context={data.globalState.selectedTargetType}
			globalState={data.globalState}
			showLinkHover={false}
			iconSize={'1.5rem'}
		/>
		{#if data.globalState.selectedTarget}
			<button class="ds-icon-btn" aria-label={$t('common.rename')} onclick={beginEditName}>
				<Pen size={16} />
			</button>
		{/if}
	</h1>
	{#snippet actions()}
		{#if data.nav.selectedConfig}
			<button
				class="ds-btn whitespace-nowrap"
				onclick={async () => {
					await saveState(data.globalState);
					await invalidateButDeferUntilNavigation((url) => url.pathname === '/api/repo_status');

					if (data.repoStatus.changes.length > 0) {
						openCommitModal = true;
					} else {
						await buildAndDownloadImage(data.nav.selectedConfig);
					}
				}}
			>
				{#if isVM}
					<Play size={'1rem'} class="min-w-4" />
					{$t('configurations.actions.build-vm-and-start')}
				{:else}
					<Download size={'1rem'} class="min-w-4" />
					{$t('configurations.actions.download')}
				{/if}
			</button>
		{/if}
	{/snippet}
</PageHead>
<Tabbar globalState={data.globalState} deploymentInfos={data.deploymentInfos} nav={data.nav} />
{@render children?.()}
