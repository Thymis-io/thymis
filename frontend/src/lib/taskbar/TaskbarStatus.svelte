<script lang="ts">
	import { run } from 'svelte/legacy';

	import { t } from 'svelte-i18n';
	import { type TaskShort } from '$lib/taskstatus';
	import { Progressbar } from 'flowbite-svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';

	interface Props {
		task: TaskShort;
		showIcons?: boolean;
		showText?: boolean;
		showProgress?: boolean;
	}

	let { task, showIcons = true, showText = true, showProgress = true }: Props = $props();

	let progress = $state(0);
	const progressScalingFunction = (done: number, expected: number) => {
		const f = (x: number) => x * x + 1;
		// if both are 0, progress is 0
		if (done === 0) {
			return 0;
		} else {
			return (f(done) / f(expected)) * 100;
		}
	};
	run(() => {
		if (task.nix_status) {
			progress = progressScalingFunction(task.nix_status.done, task.nix_status.expected);
		}
	});
</script>

<div class="flex gap-2 items-center">
	{#if task.state === 'pending'}
		{#if showIcons}
			<PendingIcon size="18" />
		{/if}
		{#if showText}
			{$t('taskbar.pending')}
		{/if}
	{:else if task.state === 'running'}
		{#if showIcons}
			<RunningIcon size="18" />
		{/if}
		{#if showText}
			{$t('taskbar.running')}
		{/if}
	{:else if task.state === 'completed'}
		{#if showIcons}
			<CompletedIcon size="18" />
		{/if}
		{#if showText}
			{$t('taskbar.completed')}
		{/if}
	{:else if task.state === 'failed'}
		{#if showIcons}
			<FailedIcon size="18" />
		{/if}
		{#if showText}
			{$t('taskbar.failed')}
		{/if}
	{:else}
		{task.state}
	{/if}
</div>
{#if showProgress && task.nix_status && task.state === 'running'}
	<Progressbar {progress} />
{/if}
