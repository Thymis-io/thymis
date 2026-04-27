<script lang="ts">
	import { t } from 'svelte-i18n';
	import Hammer from 'lucide-svelte/icons/hammer';
	import Refresh from 'lucide-svelte/icons/refresh-ccw';
	import Boxes from 'lucide-svelte/icons/boxes';
	import Box from 'lucide-svelte/icons/box';
	import Play from 'lucide-svelte/icons/play';
	import Command from 'lucide-svelte/icons/square-chevron-right';
	import RefreshCcwDot from 'lucide-svelte/icons/refresh-ccw-dot';
	import type { TaskShort } from '$lib/taskstatus';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	type DeployDeviceInfo = {
		identifier?: string;
		source_identifier?: string | null;
	};

	type DeployDeviceTaskData = {
		device?: DeployDeviceInfo;
	};

	type DeployDevicesTaskData = {
		devices?: DeployDeviceInfo[];
	};

	type ConfigurationTaskData = {
		configuration_id?: string;
	};

	interface Props {
		globalState: GlobalState;
		task: TaskShort;
		iconSize?: number;
	}

	let { globalState, task, iconSize = 18 }: Props = $props();

	const configToDisplayName = (identifier: string | undefined) => {
		if (!identifier) return '';
		const device = globalState.configs.find((config) => config.identifier === identifier);
		return device ? device.displayName : identifier;
	};

	const iconClass = 'flex-shrink-0';

	const splitSwitchLabel = (label: string) => {
		const [beforeSource, afterSource = ''] = label.split('{source}');
		const [between, afterTarget = ''] = afterSource.split('{target}');
		return { beforeSource, between, afterTarget };
	};

	const getDeployDevice = (task: TaskShort) => {
		const submissionData = task.task_submission_data as DeployDeviceTaskData | null | undefined;
		return submissionData?.device;
	};

	const getDeployDevices = (task: TaskShort) => {
		const submissionData = task.task_submission_data as DeployDevicesTaskData | null | undefined;
		return submissionData?.devices ?? [];
	};

	const getConfigurationId = (task: TaskShort) => {
		const submissionData = task.task_submission_data as ConfigurationTaskData | null | undefined;
		return submissionData?.configuration_id;
	};
</script>

<div class="flex gap-2 items-center">
	{#if task.task_type === 'project_flake_update_task'}
		<Refresh size={iconSize} class={iconClass} />
		{$t('taskbar.task-types.project_flake_update')}
	{:else if task.task_type === 'build_project_task'}
		<Hammer size={iconSize} class={iconClass} />
		{$t('taskbar.task-types.build_project')}
	{:else if task.task_type === 'deploy_devices_task'}
		<Boxes size={iconSize} class={iconClass} />
		{@const deployDevices = getDeployDevices(task)}
		{#if deployDevices.length === 1 && deployDevices[0]?.source_identifier}
			{@const switchLabel = splitSwitchLabel($t('taskbar.task-types.switch_device_config'))}
			{switchLabel.beforeSource}
			<IdentifierLink
				{globalState}
				identifier={deployDevices[0].source_identifier}
				context="config"
				{iconSize}
			/>
			{switchLabel.between}
			<IdentifierLink
				{globalState}
				identifier={deployDevices[0].identifier}
				context="config"
				{iconSize}
			/>
			{switchLabel.afterTarget}
		{:else}
			{$t('taskbar.task-types.deploy_devices')}
		{/if}
	{:else if task.task_type === 'deploy_device_task'}
		<Box size={iconSize} class={iconClass} />
		{@const deployDevice = getDeployDevice(task)}
		{#if deployDevice?.source_identifier}
			{@const switchLabel = splitSwitchLabel($t('taskbar.task-types.switch_device_config'))}
			{switchLabel.beforeSource}
			<IdentifierLink
				{globalState}
				identifier={deployDevice.source_identifier}
				context="config"
				{iconSize}
			/>
			{switchLabel.between}
			<IdentifierLink
				{globalState}
				identifier={deployDevice.identifier}
				context="config"
				{iconSize}
			/>
			{switchLabel.afterTarget}
		{:else}
			{@const [before, after] = $t('taskbar.task-types.deploy_device').split('{device}')}
			{before}
			<IdentifierLink
				{globalState}
				identifier={deployDevice?.identifier}
				context="config"
				{iconSize}
			/>
			{after}
		{/if}
	{:else if task.task_type === 'build_device_image_task'}
		<Hammer size={iconSize} class={iconClass} />
		{@const [before, after] = $t('taskbar.task-types.build_device_image').split('{device}')}
		{before}
		<IdentifierLink
			{globalState}
			identifier={getConfigurationId(task)}
			context="config"
			{iconSize}
		/>
		{after}
	{:else if task.task_type === 'ssh_command_task'}
		<Command size={iconSize} class={iconClass} />
		{$t('taskbar.task-types.ssh_command')}
	{:else if task.task_type === 'auto_update_task'}
		<RefreshCcwDot size="18" class={iconClass} />
		{$t('taskbar.task-types.auto_update')}
	{:else if task.task_type === 'run_nixos_vm_task'}
		<Play size={iconSize} class={iconClass} />
		{@const [before, after] = $t('taskbar.task-types.run_nixos_vm_task').split('{device}')}
		{before}
		<IdentifierLink
			{globalState}
			identifier={getConfigurationId(task)}
			context="config"
			{iconSize}
		/>
		{after}
	{:else}
		{task.task_type}
	{/if}
</div>
