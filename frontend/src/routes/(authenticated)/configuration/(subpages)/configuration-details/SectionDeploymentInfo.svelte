<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { isOnline, isActive } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';
	import DeploymentInstanceRow, {
		type ConfigInstance
	} from '$lib/components/DeploymentInstanceRow.svelte';
	import { Button, Select } from 'flowbite-svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import ArrowRightLeft from 'lucide-svelte/icons/arrow-right-left';
	import type { RepoStatus } from '$lib/repo/repo';

	interface Props {
		deploymentInfos?: DeploymentInfo[];
		globalState: GlobalState;
		headCommit?: string | null;
		repoStatus: RepoStatus;
		class?: string;
	}

	let {
		deploymentInfos = [],
		globalState,
		headCommit = null,
		repoStatus,
		class: className = ''
	}: Props = $props();

	// Normalise HEAD to 7-char short hash so comparisons are consistent
	// regardless of whether the caller supplies a full SHA1 or a short hash.
	let shortHead = $derived(headCommit?.slice(0, 7) ?? null);

	let instances: ConfigInstance[] = $derived(
		deploymentInfos
			.filter((di) => isActive(di.last_seen) || isOnline(di.last_seen))
			.map((di) => {
				const shortCommit = di.deployed_config_commit?.slice(0, 7) ?? null;
				return {
					id: di.id,
					online: isOnline(di.last_seen),
					active: isActive(di.last_seen),
					lastSeen: di.last_seen,
					shortCommit,
					isCurrentCommit: !!shortCommit && shortCommit === shortHead
				};
			})
			.sort((a, b) => Number(b.online) - Number(a.online))
	);

	// Per-deployment-info switch config state
	let switchConfigSelections = $state<Record<string, string>>({});
	let openCommitModal = $state(false);
	let pendingSwitch: { deploymentInfo: DeploymentInfo; newConfigId: string } | undefined = $state();

	const switchConfig = async (deploymentInfo: DeploymentInfo, newConfigId: string) => {
		const response = await fetchWithNotify(
			`/api/action/switch-config?deployment_info_id=${deploymentInfo.id}&new_config_id=${encodeURIComponent(newConfigId)}`,
			{ method: 'POST' },
			{ 409: null },
			undefined,
			[200, 409]
		);
		if (response.status === 409) {
			pendingSwitch = { deploymentInfo, newConfigId };
			openCommitModal = true;
		}
	};
</script>

<CommitModal
	bind:open={openCommitModal}
	{repoStatus}
	defaultMessage="switch config"
	onAction={async (message) => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidateButDeferUntilNavigation(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);
		if (pendingSwitch) {
			const { deploymentInfo, newConfigId } = pendingSwitch;
			pendingSwitch = undefined;
			await switchConfig(deploymentInfo, newConfigId);
		}
	}}
/>

<Section class={className} title={$t('configuration-details.deployment-info')}>
	<div class="flex flex-col gap-2 max-w-96">
		{#each instances as inst (inst.id)}
			{@const deploymentInfo = deploymentInfos.find((di) => di.id === inst.id)}
			{#if deploymentInfo}
				<DeploymentInstanceRow {inst} {globalState} {deploymentInfos} />
				{#if deploymentInfo.pending_config_id}
					{@const pendingConfig = globalState.configs.find(
						(c) => c.identifier === deploymentInfo.pending_config_id
					)}
					<p class="text-sm text-yellow-600 dark:text-yellow-400">
						{$t('configuration-details.switching-to', {
							values: { config: pendingConfig?.displayName ?? deploymentInfo.pending_config_id }
						})}
					</p>
				{/if}
				<div class="flex flex-row items-center gap-2 flex-wrap">
					<Select
						class="max-w-xs text-sm"
						items={globalState.configs
							.filter((c) => c.identifier !== deploymentInfo.deployed_config_id)
							.map((c) => ({ name: c.displayName, value: c.identifier }))}
						bind:value={switchConfigSelections[deploymentInfo.id]}
						placeholder={$t('configuration-details.switch-config-select')}
					/>
					<Button
						class="px-2 py-1.5 gap-2"
						color="alternative"
						disabled={!switchConfigSelections[deploymentInfo.id]}
						on:click={() => switchConfig(deploymentInfo, switchConfigSelections[deploymentInfo.id])}
					>
						<ArrowRightLeft size="16" />
						{$t('configuration-details.switch-config')}
					</Button>
				</div>
			{/if}
		{:else}
			<p class="text-base">{$t('configuration-details.no-deployment-info')}</p>
		{/each}
	</div>
</Section>
