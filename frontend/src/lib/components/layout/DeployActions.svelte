<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Tooltip } from 'flowbite-svelte';
	import Hammer from 'lucide-svelte/icons/hammer';
	import Refresh from 'lucide-svelte/icons/refresh-ccw';
	import Boxes from 'lucide-svelte/icons/boxes';
	import GitCommitVertical from 'lucide-svelte/icons/git-commit-vertical';
	import DeployModal from '$lib/repo/DeployModal.svelte';
	import CommitModal from '$lib/repo/CommitModal.svelte';
	import { invalidate } from '$app/navigation';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { type RepoStatus } from '$lib/repo/repo';
	import type { Nav } from '../../../routes/(authenticated)/+layout';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
	}

	let { nav, globalState, repoStatus }: Props = $props();

	const buttonClass = 'flex-auto sm:flex-[0_1_100px] gap-2 px-2 py-1.5 h-min';
	const textClass = 'text-base whitespace-nowrap';

	const build = async () => {
		await fetchWithNotify(`/api/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetchWithNotify(`/api/action/update`, { method: 'POST' });
		invalidate((url) => url.pathname === '/api/available_modules');
	};

	const commit = async (message: string) => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidate(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);
	};

	let openDeploy = $state(false);
	let openCommit = $state(false);
</script>

<div class="flex flex-wrap justify-end align-start ml-2 my-1.5 gap-1 sm:gap-2 w-[38rem]">
	<Button color="alternative" class={buttonClass} on:click={build}>
		<Hammer size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.build')}</span>
	</Button>
	<Button color="alternative" class={buttonClass} on:click={update}>
		<Refresh size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.update')}</span>
	</Button>
	<Button color="alternative" class={buttonClass} on:click={() => (openCommit = true)}>
		<div class="flex">
			<GitCommitVertical size={'1rem'} class="min-w-4" />
			<span class="pt-1">
				{repoStatus.changes.length}
			</span>
		</div>
		<span class={textClass}>{$t('deploy.commit')}</span>
	</Button>
	<Button color="alternative" class={buttonClass} on:click={() => (openDeploy = true)}>
		<Boxes size={'1rem'} class="min-w-4" />
		<span class={textClass}>{$t('deploy.deploy')}</span>
	</Button>
	<DeployModal bind:open={openDeploy} {repoStatus} {globalState} {nav} />
	<CommitModal bind:open={openCommit} {repoStatus} onAction={commit} />
</div>
