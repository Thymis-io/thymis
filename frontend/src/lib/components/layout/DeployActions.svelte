<script lang="ts">
	import { t } from 'svelte-i18n';
	import Hammer from 'lucide-svelte/icons/hammer';
	import Refresh from 'lucide-svelte/icons/refresh-ccw';
	import Boxes from 'lucide-svelte/icons/boxes';
	import GitCommitVertical from 'lucide-svelte/icons/git-commit-vertical';
	import DeployModal from '$lib/repo/DeployModal.svelte';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { type RepoStatus } from '$lib/repo/repo';
	import type { Nav } from '../../../routes/(authenticated)/+layout';
	import type { GlobalState } from '$lib/state.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		selectedDeploymentInfo?: DeploymentInfo | undefined;
	}

	let { nav, globalState, repoStatus, selectedDeploymentInfo = undefined }: Props = $props();

	const textClass = 'whitespace-nowrap';

	const build = async () => {
		await fetchWithNotify(`/api/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetchWithNotify(`/api/action/update`, { method: 'POST' });
		invalidateButDeferUntilNavigation((url) => url.pathname === '/api/available_modules');
	};

	const commit = async (message: string) => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidateButDeferUntilNavigation(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);
	};

	let openDeploy = $state(false);
	let openCommit = $state(false);
</script>

<div class="flex flex-wrap items-center justify-end gap-1 sm:gap-2">
	<button class="ds-btn" onclick={build}>
		<Hammer size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.build')}</span>
	</button>
	<button class="ds-btn" onclick={update}>
		<Refresh size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.update')}</span>
	</button>
	<button class="ds-btn" onclick={() => (openCommit = true)}>
		<span class="flex items-center">
			<GitCommitVertical size={'1rem'} class="min-w-4" />
			<span>{repoStatus.changes.length}</span>
		</span>
		<span class={textClass}>{$t('deploy.commit')}</span>
	</button>
	<button class="ds-btn" onclick={() => (openDeploy = true)}>
		<Boxes size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.deploy')}</span>
	</button>
	<DeployModal bind:open={openDeploy} {repoStatus} {globalState} {nav} {selectedDeploymentInfo} />
	<CommitModal bind:open={openCommit} {repoStatus} onAction={commit} />
</div>
