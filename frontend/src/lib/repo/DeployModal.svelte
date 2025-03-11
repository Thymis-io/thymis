<script lang="ts">
	import { run } from 'svelte/legacy';

	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { Button, Modal, Input, Tooltip } from 'flowbite-svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { type Config, type Tag } from '$lib/state';
	import FloatingMultiSelect from '$lib/components/FloatingMultiSelect.svelte';
	import type { RepoStatus } from '$lib/repo/repo';
	import FileChanges from './FileChanges.svelte';
	import type { ObjectOption } from 'svelte-multiselect';
	import type { Nav } from '../../routes/(authenticated)/+layout';
	import { invalidateButDeferUntilNavigation } from '$lib/notification';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		open?: boolean;
	}

	let { nav, globalState, repoStatus, open = $bindable(false) }: Props = $props();

	let message = $state('deploy');
	let selectedFile = $state('');
	let hasFileChanges = $derived(repoStatus.changes.length > 0);

	type MyOption = {
		type: 'tag' | 'config';
		value: string;
		label: string;
		icon: any;
	} & ObjectOption;

	const toOption = (target: Config | Tag, type: 'tag' | 'config'): MyOption => {
		return {
			type: type,
			value: target.identifier,
			label: target.displayName,
			icon: type === 'tag' ? TagIcon : FileCode
		};
	};
	const toOptionList = (options: any[]): MyOption[] => options as MyOption[];

	let selectedOptions: MyOption[] = $state([]);
	let affectedConfigs: Config[] = $state([]);
	run(() => {
		const configs = selectedOptions.filter((opt) => opt.type === 'config').map((opt) => opt.value);
		const tags = selectedOptions.filter((opt) => opt.type === 'tag').map((opt) => opt.value);

		affectedConfigs = globalState.configs.filter((config) => {
			return configs.includes(config.identifier) || config.tags.some((tag) => tags.includes(tag));
		});
	});

	const commit = async () => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidateButDeferUntilNavigation(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);
		message = '';
	};

	const deploy = async () => {
		const configs = affectedConfigs.map((config) => '&config=' + config.identifier).join('');
		await fetchWithNotify(`/api/action/deploy?${configs}`, {
			method: 'POST'
		});
		await invalidateButDeferUntilNavigation((url) => url.pathname === '/api/history');
	};
</script>

<Modal
	bind:open
	title={$t('deploy.deploy')}
	size="xl"
	outsideclose
	on:open={() => {
		selectedFile = 'state.json';
		if (nav.selectedTarget && nav.selectedTargetType) {
			selectedOptions = [toOption(nav.selectedTarget, nav.selectedTargetType)];
		} else {
			selectedOptions = [];
		}
	}}
>
	<div class={'flex flex-col gap-8 ' + (hasFileChanges ? 'h-[60vh]' : '')}>
		{#if hasFileChanges}
			<div>
				<p class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.summary')}</p>
				<Input
					type="text"
					bind:value={message}
					placeholder={$t('deploy.summary')}
					disabled={repoStatus.changes.length === 0}
				/>
			</div>
			<p class="text-base text-gray-900 dark:text-white mb-[-2em]">{$t('deploy.open-changes')}</p>
			<FileChanges {repoStatus} {selectedFile} />
		{:else}
			<p class="text-base text-gray-900 dark:text-white">{$t('deploy.no-changes')}</p>
		{/if}
		<div class="flex flex-row gap-4">
			<div class="flex-1">
				<div class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.selected')}</div>
				<FloatingMultiSelect
					options={toOptionList(
						Array.prototype.concat(
							globalState.tags.map((tag) => toOption(tag, 'tag')),
							globalState.configs.map((config) => toOption(config, 'config'))
						)
					)}
					bind:selected={selectedOptions}
					outerDivClass="w-full"
				>
					{#snippet children({ option })}
						<div class="flex gap-1 items-center text-base text-gray-900 dark:text-white">
							<option.icon size={16} />
							{option.label}
						</div>
					{/snippet}
				</FloatingMultiSelect>
				<Button
					color="alternative"
					class="mt-2 float-right"
					on:click={() => {
						selectedOptions = Array.prototype.concat(
							selectedOptions.filter((opt) => opt.type === 'tag'),
							globalState.configs.map((config) => toOption(config, 'config'))
						);
					}}
				>
					{$t('deploy.add-all-configs')}
				</Button>
			</div>
			<div class="flex-0 inline-block w-0.5 self-stretch bg-neutral-100 dark:bg-white/10"></div>
			<div class="flex-1 flex flex-col gap-2 text-base text-gray-900 dark:text-white">
				<div class="mb-1">{$t('deploy.configurations')}</div>
				<div class="flex flex-wrap flex-row gap-2">
					{#each affectedConfigs as config}
						<div
							class={'flex items-center text-white bg-primary-700 dark:bg-primary-600 rounded p-2 py-0.5 gap-1'}
						>
							<FileCode size={'0.8rem'} class="min-w-3" />
							{config.displayName}
						</div>
					{/each}
				</div>
				<div class="mt-auto ml-auto">
					{#if hasFileChanges}
						<Button
							on:click={async () => {
								await commit();
								await deploy();
								open = false;
							}}
							disabled={affectedConfigs.length === 0 || message.length === 0}
							class="w-48"
						>
							{$t('deploy.commit-deploy')}
						</Button>
					{:else}
						<div class="mt-auto">
							<Button
								on:click={() => {
									deploy();
									open = false;
								}}
								disabled={affectedConfigs.length === 0}
								class="w-48"
							>
								{$t('deploy.deploy')}
							</Button>
						</div>
					{/if}
					{#if affectedConfigs.length === 0}
						<Tooltip>
							{$t('deploy.no-affected-configs-tooltip')}
						</Tooltip>
					{/if}
				</div>
			</div>
		</div>
	</div>
</Modal>

<style>
	:root {
		--sms-options-max-height: 12em;
	}
</style>
