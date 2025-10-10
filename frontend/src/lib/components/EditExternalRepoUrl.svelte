<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FlakeReference } from '$lib/externalRepo';
	import { Modal, Label, Input, Select, Button, Spinner } from 'flowbite-svelte';
	import AutoComplete from './AutoComplete.svelte';
	import Branch from 'lucide-svelte/icons/git-branch';
	import Commit from 'lucide-svelte/icons/git-commit-vertical';
	import Tag from 'lucide-svelte/icons/tag';
	import Warning from 'lucide-svelte/icons/triangle-alert';
	import RefreshCcw from 'lucide-svelte/icons/refresh-ccw';
	import Check from 'lucide-svelte/icons/check';
	import X from 'lucide-svelte/icons/x';
	import RepoConnectionTest from './RepoConnectionTest.svelte';

	interface Props {
		open?: boolean;
		inputName?: string;
		inputUrl?: string;
		apiSecret?: string | null;
		onSave: (newUrl: string) => void;
		onClose: () => void;
	}

	let {
		open = $bindable(false),
		inputName,
		inputUrl,
		apiSecret,
		onSave,
		onClose
	}: Props = $props();

	let testConnectionUrl = $state<string>('');

	let flakeReference = $state<FlakeReference>();
	let compiledUrl = $derived.by(() => {
		if (!flakeReference) return '';
		if (flakeReference.type === 'git') {
			const protocol =
				flakeReference.protocol && flakeReference.protocol !== 'git'
					? `+${flakeReference.protocol}://`
					: ':';
			const host = flakeReference.host;
			const ref = flakeReference.ref ? `?ref=${flakeReference.ref}` : '';
			const rev = flakeReference.rev ? `?rev=${flakeReference.rev}` : '';
			if (flakeReference.protocol === 'file') {
				return `git+file://${flakeReference.url}`;
			} else {
				return `git${protocol}${host}/${flakeReference.owner}/${flakeReference.repo}.git${ref}${rev}`;
			}
		} else if (flakeReference.type === 'github') {
			const ref = flakeReference.ref ? `/${flakeReference.ref}` : '';
			const rev = flakeReference.rev ? `/${flakeReference.rev}` : '';
			return `github:${flakeReference.owner}/${flakeReference.repo}${ref}${rev}`;
		} else if (flakeReference.type === 'gitlab') {
			const ref = flakeReference.ref ? `/${flakeReference.ref}` : '';
			const rev = flakeReference.rev ? `/${flakeReference.rev}` : '';
			return `gitlab:${flakeReference.owner}/${flakeReference.repo}${ref}${rev}`;
		}
	});

	let manualRefRefreshStatus = $state<null | 'pending' | 'done' | 'error'>(null);
	let repoBranches = $state<{ name: string }[]>([]);
	let repoTags = $state<{ name: string }[]>([]);

	const loadRepo = async (name: string) => {
		flakeReference = undefined;

		const [flakeRefFetch] = await Promise.all([
			fetch(`/api/external-repositories/flake-ref/${name}`)
		]);

		if (flakeRefFetch.ok) {
			flakeReference = await flakeRefFetch.json();
		}
	};

	const loadRefs = async (url: string) => {
		repoBranches = [];
		repoTags = [];

		const searchParams = new URLSearchParams();
		if (apiSecret) {
			searchParams.set('api_key_secret', apiSecret);
		}

		const [branchesFetch, tagsFetch] = await Promise.all([
			fetch(`/api/external-repositories/branches/${encodeURIComponent(url)}?${searchParams}`),
			fetch(`/api/external-repositories/tags/${encodeURIComponent(url)}?${searchParams}`)
		]);

		if (branchesFetch.ok) {
			repoBranches = await branchesFetch.json();
		}

		if (tagsFetch.ok) {
			repoTags = await tagsFetch.json();
		}

		return branchesFetch.ok && tagsFetch.ok;
	};

	const onBranchSelect = (value: string) => {
		if (!flakeReference) return;
		if (value.length === 40) {
			flakeReference.ref = null;
			flakeReference.rev = value;
		} else {
			flakeReference.ref = value;
			flakeReference.rev = null;
		}
	};

	const isCommitSha = (value: string) => {
		return /^[0-9a-f]{40}$/.test(value);
	};

	const warnings = $derived.by(() => {
		const warns: string[] = [];
		if (!flakeReference) return warns;
		if (flakeReference.type === 'git' && flakeReference.host?.includes('github.com')) {
			warns.push($t('settings.external-modal.use-github-warning'));
		}
		if (flakeReference.type === 'git' && flakeReference.host?.includes('gitlab.com')) {
			warns.push($t('settings.external-modal.use-gitlab-warning'));
		}
		if (
			flakeReference.type === 'git' &&
			flakeReference.protocol === 'file' &&
			!flakeReference.url?.startsWith('/')
		) {
			warns.push($t('settings.external-modal.file-not-absolute-warning'));
		}
		return warns;
	});
</script>

<Modal
	bind:open
	title={$t('settings.external-modal.title')}
	size="lg"
	on:open={() => {
		testConnectionUrl = '';
		manualRefRefreshStatus = null;
		if (inputName) loadRepo(inputName);
		if (inputUrl) loadRefs(inputUrl);
	}}
	on:close={() => {
		testConnectionUrl = '';
		onClose();
	}}
>
	{#if flakeReference}
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">{$t('settings.external-modal.reference-type')}</Label>
				<Select
					value={flakeReference.type}
					class="mb-2"
					on:change={(e) => {
						const newType = (e.target as HTMLInputElement)?.value ?? '';
						const prevType = flakeReference?.type;
						if (!newType || !flakeReference) return;

						if (newType === 'git') {
							const gitRef = flakeReference as Extract<FlakeReference, { type: 'git' }>;

							if (prevType === 'github') {
								gitRef.host ??= 'github.com';
								gitRef.protocol ??= 'https';
							} else if (prevType === 'gitlab') {
								gitRef.host ??= 'gitlab.com';
								gitRef.protocol ??= 'https';
							}

							gitRef.type = 'git';
						} else {
							flakeReference.type = newType as FlakeReference['type'];
						}
					}}
				>
					<option value="git">{$t('settings.external-modal.reference-type-git')}</option>
					<option value="github">{$t('settings.external-modal.reference-type-github')}</option>
					<option value="gitlab">{$t('settings.external-modal.reference-type-gitlab')}</option>
				</Select>
			</div>
			<div class="flex-5">
				{#if warnings.length > 0}
					<div class="text-yellow-600 dark:text-yellow-400 flex items-top gap-2 text-base mt-6">
						<Warning class="w-5 h-5 flex-shrink-0" />
						<div>
							{#each warnings as warn}
								<div>{warn}</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
	{#if flakeReference && flakeReference.type === 'git'}
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">{$t('settings.external-modal.protocol')}</Label>
				<Select
					bind:value={flakeReference.protocol}
					on:change={(e) => {
						const protocol = (e.target as HTMLInputElement)?.value ?? '';
						if (!protocol || !flakeReference || flakeReference.type !== 'git') return;
						if (
							(protocol === 'http' || protocol === 'https' || protocol === 'git') &&
							flakeReference.host
						) {
							flakeReference.host = flakeReference.host.replace(/^(git@)/, '');
						} else if (
							protocol === 'ssh' &&
							flakeReference.host &&
							!flakeReference.host.includes('@')
						) {
							flakeReference.host = 'git@' + flakeReference.host;
						} else if (protocol === 'file') {
							flakeReference.host = '';
							flakeReference.url = '/path/to/repo';
						}
					}}
					class="mb-2"
				>
					<option value="http">{$t('settings.external-modal.protocol-http')}</option>
					<option value="https">{$t('settings.external-modal.protocol-https')}</option>
					<option value="ssh">{$t('settings.external-modal.protocol-ssh')}</option>
					<option value="git">{$t('settings.external-modal.protocol-git')}</option>
					<option value="file">{$t('settings.external-modal.protocol-file')}</option>
				</Select>
			</div>
			<div class="flex-5">
				{#if flakeReference.protocol !== 'file'}
					<Label class="mb-0">{$t('settings.external-modal.host')}</Label>
					<Input class="mb-2" bind:value={flakeReference.host} />
				{:else}
					<Label class="mb-0">{$t('settings.external-modal.file-path')}</Label>
					<Input class="mb-2" bind:value={flakeReference.url} />
				{/if}
			</div>
		</div>
	{/if}
	{#if flakeReference && ((flakeReference.type === 'git' && flakeReference.protocol !== 'file') || flakeReference.type === 'github' || flakeReference.type === 'gitlab')}
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">{$t('settings.external-modal.owner')}</Label>
				<Input bind:value={flakeReference.owner} class="mb-2" />
			</div>
			<div class="flex-1">
				<Label class="mb-0">{$t('settings.external-modal.repo')}</Label>
				<Input bind:value={flakeReference.repo} class="mb-2" />
			</div>
		</div>
	{/if}
	{#if flakeReference && (flakeReference.type === 'git' || flakeReference.type === 'github' || flakeReference.type === 'gitlab')}
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">{$t('settings.external-modal.ref')}</Label>
				<AutoComplete
					value={flakeReference.ref ?? flakeReference.rev ?? ''}
					options={[
						...repoBranches.map((branch) => ({
							label: branch.name,
							value: branch.name,
							icon: Branch
						})),
						...repoTags.map((tag) => ({
							label: tag.name,
							value: tag.name,
							icon: Tag
						}))
					]}
					allowCustomValues={true}
					onChange={onBranchSelect}
					defaultIcon={(value: string) => (isCommitSha(value) ? Commit : undefined)}
				/>
			</div>
			<div class="flex-1">
				<Button
					on:click={() => {
						if (compiledUrl) {
							manualRefRefreshStatus = 'pending';
							loadRefs(compiledUrl).then((success) => {
								manualRefRefreshStatus = success ? 'done' : 'error';
								setTimeout(() => (manualRefRefreshStatus = null), 3000);
							});
						}
					}}
					class="gap-1 mt-4 px-3"
					color="alternative"
				>
					{#if !manualRefRefreshStatus}
						<RefreshCcw class="w-4 h-4" />
					{:else if manualRefRefreshStatus === 'pending'}
						<Spinner class="w-4 h-4" />
					{:else if manualRefRefreshStatus === 'done'}
						<Check class="w-4 h-4 text-green-500" />
					{:else if manualRefRefreshStatus === 'error'}
						<X class="w-4 h-4 text-red-500" />
					{/if}
					{$t('settings.external-modal.refresh-refs')}
				</Button>
			</div>
		</div>
	{/if}
	{#if flakeReference}
		<div class="flex mt-8 gap-2">
			<div class="flex-5">
				<Label class="mb-0">{$t('settings.external-modal.compiled-url')}</Label>
				<Input class="flex-6 mb-2 w-full" bind:value={compiledUrl} placeholder="Repository URL" />
			</div>
			<Button
				class="flex-1 mt-4 mb-2"
				on:click={() => {
					if (compiledUrl) {
						testConnectionUrl = '';
						testConnectionUrl = compiledUrl;
					}
				}}
				disabled={!compiledUrl}
			>
				{$t('settings.repo.check')}
			</Button>
			<Button
				class="flex-1 mt-4 mb-2"
				on:click={() => {
					if (compiledUrl) onSave(compiledUrl);
					open = false;
				}}
				disabled={!compiledUrl}
			>
				{$t('common.save')}
			</Button>
		</div>
	{/if}
	{#if !flakeReference}
		<div class="flex justify-center mt-4">
			<Spinner class="mr-2" size="8" />
		</div>
	{/if}
	<RepoConnectionTest inputUrl={testConnectionUrl} {apiSecret} />
</Modal>
