<script lang="ts">
	import { t } from 'svelte-i18n';
	import Hammer from 'lucide-svelte/icons/hammer';
	import Refresh from 'lucide-svelte/icons/refresh-ccw';
	import Boxes from 'lucide-svelte/icons/boxes';
	import Box from 'lucide-svelte/icons/box';
	import Play from 'lucide-svelte/icons/play';
	import Command from 'lucide-svelte/icons/square-chevron-right';
	import type { TaskShort } from '$lib/taskstatus';
	import { state } from '$lib/state';

	export let task: TaskShort;

	const configToDisplayName = (identifier: string | undefined) => {
		if (!identifier) return '';
		const device = $state.configs.find((config) => config.identifier === identifier);
		return device ? device.displayName : identifier;
	};

	const iconClass = 'flex-shrink-0';
</script>

<div class="flex gap-2 items-center">
	{#if task.task_type === 'project_flake_update_task'}
		<Refresh size="18" class={iconClass} />
		{$t('taskbar.task-types.project_flake_update')}
	{:else if task.task_type === 'build_project_task'}
		<Hammer size="18" class={iconClass} />
		{$t('taskbar.task-types.build_project')}
	{:else if task.task_type === 'deploy_devices_task'}
		<Boxes size="18" class={iconClass} />
		{$t('taskbar.task-types.deploy_devices')}
	{:else if task.task_type === 'deploy_device_task'}
		{@const displayName = configToDisplayName(task.task_submission_data?.device?.identifier)}
		<Box size="18" class={iconClass} />
		{$t('taskbar.task-types.deploy_device', { values: { device: displayName } })}
	{:else if task.task_type === 'build_device_image_task'}
		{@const displayName = configToDisplayName(task.task_submission_data?.configuration_id)}
		<Hammer size="18" class={iconClass} />
		{$t('taskbar.task-types.build_device_image', { values: { device: displayName } })}
	{:else if task.task_type === 'ssh_command_task'}
		<Command size="18" class={iconClass} />
		{$t('taskbar.task-types.ssh_command')}
	{:else if task.task_type === 'run_nixos_vm_task'}
		{@const displayName = configToDisplayName(task.task_submission_data?.configuration_id)}
		<Play size="18" class={iconClass} />
		{$t('taskbar.task-types.run_nixos_vm_task', { values: { device: displayName } })}
	{:else}
		{task.task_type}
	{/if}
</div>
