<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from '$lib/components/layout/Section.svelte';
	import type { Config } from '$lib/state';
	import type { GlobalState } from '$lib/state.svelte';
	import { type DeploymentInfo, isOnline } from '$lib/deploymentInfo';
	import type { RepoStatus } from '$lib/repo/repo';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import ArrowRightLeft from 'lucide-svelte/icons/arrow-right-left';
	import { Select } from 'flowbite-svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import { getDeviceType } from '$lib/config/configUtils';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		deploymentInfo: DeploymentInfo;
		config: Config | undefined;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		class?: string;
	}

	let { deploymentInfo, config, globalState, repoStatus, class: className = '' }: Props = $props();

	let online = $derived(isOnline(deploymentInfo.last_seen));

	const restartDevice = async () => {
		if (!config) return;
		await fetchWithNotify(`/api/action/restart-device?identifier=${config.identifier}`, {
			method: 'POST'
		});
	};

	// Configs of the same device type the device can be switched to.
	let switchableConfigs = $derived.by(() => {
		const sourceDeviceType = getDeviceType(config);
		if (!sourceDeviceType) return [];
		return globalState.configs.filter(
			(c) =>
				c.identifier !== deploymentInfo.deployed_config_id && getDeviceType(c) === sourceDeviceType
		);
	});

	let switchSelection = $state('');
	let openCommitModal = $state(false);
	let pendingSwitch = $state(false);

	const switchConfig = async (newConfigId: string) => {
		const response = await fetchWithNotify(
			`/api/action/switch-config?deployment_info_id=${deploymentInfo.id}&new_config_id=${encodeURIComponent(newConfigId)}`,
			{ method: 'POST' },
			{ 409: null },
			undefined,
			[200, 409]
		);
		if (response.status === 409) {
			pendingSwitch = true;
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
		if (pendingSwitch && switchSelection) {
			pendingSwitch = false;
			await switchConfig(switchSelection);
		}
	}}
/>

<Section class={className} title={$t('configuration-details.actions')}>
	<div class="flex flex-col gap-4">
		<button class="ds-btn justify-start self-start" onclick={restartDevice}>
			<RotateCcw size={'1rem'} class="min-w-4" />
			{$t('configurations.actions.restart')}
		</button>

		{#if online && switchableConfigs.length > 0}
			<div class="flex flex-col gap-2">
				<Select
					class="text-sm"
					items={switchableConfigs.map((c) => ({ name: c.displayName, value: c.identifier }))}
					bind:value={switchSelection}
					placeholder={$t('configuration-details.switch-config-select')}
				/>
				<button
					class="ds-btn ds-btn-sm self-start disabled:cursor-not-allowed disabled:opacity-50"
					disabled={!switchSelection}
					onclick={() => switchConfig(switchSelection)}
				>
					<ArrowRightLeft size="16" />
					{$t('configuration-details.switch-config')}
				</button>
				{#if deploymentInfo.pending_config_id}
					{@const [before, after] = $t('configuration-details.switching-to').split('{config}')}
					<div class="text-sm text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
						{before}
						<IdentifierLink
							{globalState}
							identifier={deploymentInfo.pending_config_id}
							context="config"
						/>
						{after}
					</div>
				{/if}
			</div>
		{/if}
	</div>
</Section>
