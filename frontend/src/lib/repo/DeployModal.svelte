<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
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
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import { type DeploymentInfo, isOnline } from '$lib/deploymentInfo';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		open?: boolean;
		selectedDeploymentInfo?: DeploymentInfo | undefined;
	}

	let {
		nav,
		globalState,
		repoStatus,
		open = $bindable(false),
		selectedDeploymentInfo = undefined
	}: Props = $props();

	let message = $state('deploy');
	let selectedFile = $state('');
	let hasFileChanges = $derived(repoStatus.changes.length > 0);

	type MyOption = {
		type: 'tag' | 'config' | 'device';
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

	const deviceLabel = (device: DeploymentInfo): string => {
		if (device.name) return device.name;
		const config = globalState.configs.find((c) => c.identifier === device.deployed_config_id);
		return config ? `${device.id} (${config.displayName})` : device.id;
	};

	const toDeviceOption = (device: DeploymentInfo): MyOption => ({
		type: 'device',
		value: device.id,
		label: deviceLabel(device),
		icon: HardDrive
	});

	const toOptionList = (options: any[]): MyOption[] => options as MyOption[];

	let selectedOptions: MyOption[] = $state([]);

	let configsFromSelections = $derived.by(() => {
		const configIds = selectedOptions
			.filter((opt) => opt.type === 'config')
			.map((opt) => opt.value);
		const tagIds = selectedOptions.filter((opt) => opt.type === 'tag').map((opt) => opt.value);
		return globalState.configs.filter(
			(config) =>
				configIds.includes(config.identifier) || config.tags.some((tag) => tagIds.includes(tag))
		);
	});

	let selectedDeviceIds = $derived(
		selectedOptions.filter((opt) => opt.type === 'device').map((opt) => opt.value)
	);

	let affectedDevices = $derived.by(() => {
		const affectedConfigIdSet = new Set(configsFromSelections.map((c) => c.identifier));
		const seen = new Set<string>();
		const result: DeploymentInfo[] = [];
		for (const d of [
			...globalState.deploymentInfos.filter(
				(d) => d.deployed_config_id !== null && affectedConfigIdSet.has(d.deployed_config_id!)
			),
			...globalState.deploymentInfos.filter((d) => selectedDeviceIds.includes(d.id))
		]) {
			if (!seen.has(d.id) && isOnline(d.last_seen)) {
				seen.add(d.id);
				result.push(d);
			}
		}
		return result;
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
		const configParams = configsFromSelections
			.map((config) => '&config=' + config.identifier)
			.join('');
		const deviceParams = selectedDeviceIds.map((id) => '&deployment_info_id=' + id).join('');
		await fetchWithNotify(`/api/action/deploy?${configParams}${deviceParams}`, {
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
		message = 'deploy';
		if (selectedDeploymentInfo) {
			selectedOptions = [toDeviceOption(selectedDeploymentInfo)];
		} else if (nav.selectedTarget && nav.selectedTargetType) {
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
							globalState.configs.map((config) => toOption(config, 'config')),
							globalState.deploymentInfos.map(toDeviceOption)
						)
					)}
					key={(option: MyOption) => option.type + option.value}
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
				<div class="mb-1">{$t('deploy.affected-devices')}</div>
				<div class="flex flex-wrap flex-row gap-2">
					{#each affectedDevices as device}
						<IdentifierLink
							identifier={device.id}
							context="device"
							deploymentInfo={device}
							{globalState}
							solidBackground
							showConfigNameForDevice
						/>
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
							disabled={affectedDevices.length === 0 || message.length === 0}
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
								disabled={affectedDevices.length === 0}
								class="w-48"
							>
								{$t('deploy.deploy')}
							</Button>
						</div>
					{/if}
					{#if affectedDevices.length === 0}
						<Tooltip>
							{$t('deploy.no-targets-tooltip')}
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
