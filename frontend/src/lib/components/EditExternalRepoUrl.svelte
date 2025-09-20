<script lang="ts">
	import type { FlakeReference } from '$lib/externalRepo';
	import { Modal, Label, Input, Select } from 'flowbite-svelte';
	import AutoComplete from './AutoComplete.svelte';
	import Branch from 'lucide-svelte/icons/git-branch';
	import Commit from 'lucide-svelte/icons/git-commit-vertical';

	interface Props {
		open?: boolean;
		inputName: string;
		url?: string;
		onSave?: (newUrl: string) => void;
	}

	let { open = $bindable(false), inputName, url = $bindable(''), onSave }: Props = $props();

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
			return `git${protocol}${host}/${flakeReference.owner}/${flakeReference.repo}${ref}${rev}`;
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

	let repoBranches = $state<{ name: string }[]>([]);

	$effect(() => {
		if (!inputName) return;
		loadRepo(inputName);
	});

	const loadRepo = async (name: string) => {
		flakeReference = await (await fetch(`/api/external-repositories/flake-ref/${name}`)).json();
		repoBranches = await (await fetch(`/api/external-repositories/branches/${name}`)).json();
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
</script>

<Modal bind:open title="Edit External Repository URL" size="lg" outsideclose>
	{#if flakeReference}
		<div class="flex gap-2">
			<div>
				<Label for="type" class="mb-0">Type</Label>
				<Select bind:value={flakeReference.type} class="mb-2">
					<option value="git">git</option>
					<option value="github">github</option>
					<option value="gitlab">gitlab</option>
				</Select>
			</div>
		</div>
	{/if}
	{#if flakeReference && flakeReference.type === 'git'}
		<div class="flex gap-2">
			<div>
				<Label class="mb-0">Protocol</Label>
				<Select
					bind:value={flakeReference.protocol}
					on:change={(e) => {
						const protocol = (e.target as HTMLInputElement)?.value ?? '';
						if (!protocol || !flakeReference || flakeReference.type !== 'git') return;
						if (protocol === 'http' || protocol === 'https' || protocol === 'git') {
							flakeReference.host = flakeReference.host.replace(/^(git@)/, '');
						} else if (protocol === 'ssh') {
							if (!flakeReference.host.startsWith('git@')) {
								flakeReference.host = 'git@' + flakeReference.host;
							}
						}
					}}
					class="mb-2"
				>
					<option value="http">https</option>
					<option value="https">https</option>
					<option value="ssh">ssh</option>
					<option value="git">git</option>
				</Select>
			</div>
			<div class="flex-1">
				<Label class="mb-0">Host</Label>
				<Input bind:value={flakeReference.host} class="mb-2" />
			</div>
		</div>
	{/if}
	{#if flakeReference && (flakeReference.type === 'git' || flakeReference.type === 'github' || flakeReference.type === 'gitlab')}
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">Owner</Label>
				<Input bind:value={flakeReference.owner} class="mb-2" />
			</div>
			<div class="flex-1">
				<Label class="mb-0">Repository</Label>
				<Input bind:value={flakeReference.repo} class="mb-2" />
			</div>
		</div>
		<div class="flex gap-2">
			<div class="flex-1">
				<Label class="mb-0">Ref / Branch / Tag / Full Commit SHA (optional)</Label>
				<AutoComplete
					value={flakeReference.ref ?? flakeReference.rev ?? ''}
					values={repoBranches.map((branch) => ({
						label: branch.name,
						value: branch.name,
						icon: Branch
					}))}
					allowCustomValues={true}
					onChange={onBranchSelect}
					defaultIcon={(value: string) => (isCommitSha(value) ? Commit : undefined)}
				/>
			</div>
			<div class="flex-1"></div>
		</div>
	{/if}
	<br />
	<Input bind:value={compiledUrl} placeholder="Repository URL" class="mb-2 w-full" />
</Modal>
