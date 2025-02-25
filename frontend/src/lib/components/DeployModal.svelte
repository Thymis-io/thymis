<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { Button, Modal, Input, Tooltip } from 'flowbite-svelte';
	import { invalidate } from '$app/navigation';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import {
		globalNavSelectedTarget,
		globalNavSelectedTargetType,
		state,
		type Config,
		type Tag
	} from '$lib/state';
	import MultiSelect from 'svelte-multiselect';
	import type { RepoStatus } from '$lib/repo/repo';

	export let repoStatus: RepoStatus;
	export let open = false;

	type Option = {
		type: 'tag' | 'config';
		value: string;
		label: string;
		icon: any;
	};

	const defaultSelectedOption = (
		globalNavSelectedTarget: Config | Tag | undefined,
		globalNavSelectedTargetType: string | null
	): Option[] => {
		if (globalNavSelectedTargetType === 'config' && globalNavSelectedTarget) {
			return [
				{
					type: 'config',
					value: globalNavSelectedTarget.identifier,
					label: globalNavSelectedTarget.displayName,
					icon: FileCode
				}
			];
		} else if (globalNavSelectedTargetType === 'tag' && globalNavSelectedTarget) {
			return [
				{
					type: 'tag',
					value: globalNavSelectedTarget.identifier,
					label: globalNavSelectedTarget.displayName,
					icon: TagIcon
				}
			];
		}
		return [];
	};

	let selectedOptions = defaultSelectedOption(
		$globalNavSelectedTarget,
		$globalNavSelectedTargetType
	);

	let filteredConfigs: Config[];
	$: {
		const configs = selectedOptions.filter((opt) => opt.type === 'config').map((opt) => opt.value);
		const tags = selectedOptions.filter((opt) => opt.type === 'tag').map((opt) => opt.value);

		filteredConfigs = Object.values($state.configs).filter(
			(config) =>
				configs.includes(config.identifier) || config.tags.some((tag) => tags.includes(tag))
		);
	}

	const deploy = async () => {
		const configs = filteredConfigs.map((config) => '&config=' + config.identifier).join('');
		await fetchWithNotify(`/api/action/deploy?${configs}`, {
			method: 'POST'
		});
		await invalidate((url) => url.pathname === '/api/history');

		open = false;
	};
</script>

<Modal
	bind:open
	title={$t('deploy.deploy')}
	size="lg"
	outsideclose
	on:open={() => {
		selectedOptions = defaultSelectedOption($globalNavSelectedTarget, $globalNavSelectedTargetType);
	}}
>
	<div class="min-h-12">
		<div class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.selected')}</div>
		<MultiSelect
			options={Array.prototype.concat(
				Object.values($state.tags).map((tag) => ({
					type: 'tag',
					value: tag.identifier,
					label: tag.displayName,
					icon: TagIcon
				})),
				Object.values($state.configs).map((config) => ({
					type: 'config',
					value: config.identifier,
					label: config.displayName,
					icon: FileCode
				}))
			)}
			bind:selected={selectedOptions}
			outerDivClass="w-full"
			let:option
		>
			<div class="flex gap-1 items-center text-base text-gray-900 dark:text-white">
				<svelte:component this={option.icon} size={16} />{option.label}
			</div>
		</MultiSelect>
	</div>
	<div class="min-h-32 text-base text-gray-900 dark:text-white">
		<div class="mb-1">{$t('deploy.configurations')}</div>
		<div class="flex flex-wrap flex-row gap-2">
			{#each filteredConfigs as config}
				<div
					class={'flex items-center text-white bg-primary-700 dark:bg-primary-600 rounded p-2 py-0.5 gap-1'}
				>
					<FileCode size={'0.8rem'} class="min-w-3" />
					{config.displayName}
				</div>
			{/each}
		</div>
	</div>
	<div class="flex flex-wrap gap-2 justify-end">
		<Button
			on:click={deploy}
			disabled={filteredConfigs.length === 0 || repoStatus.changes.length > 0}
		>
			{$t('deploy.deploy')}
		</Button>
		{#if filteredConfigs.length === 0 || repoStatus.changes.length > 0}
			<Tooltip defaultClass="py-2 px-3 w-80 text-sm font-medium z-50">
				{#if filteredConfigs.length === 0}
					<p>{$t('deploy.no-affected-configs-tooltip')}</p>
				{/if}
				{#if repoStatus.changes.length > 0}
					<p>{$t('deploy.dirty-repo-tooltip')}</p>
				{/if}
			</Tooltip>
		{/if}
	</div>
</Modal>

<style>
	:root {
		--sms-options-max-height: 12em;
	}
</style>
