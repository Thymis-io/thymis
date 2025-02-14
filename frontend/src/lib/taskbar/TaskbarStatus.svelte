<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort } from '$lib/taskstatus';
	export let task: TaskShort;
	import { Progressbar } from 'flowbite-svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';

	let progress = 0;
	const progressScalingFunction = (done: number, expected: number) => {
		const f = (x: number) => x * x + 1;
		// if both are 0, progress is 0
		if (done === 0) {
			return 0;
		} else {
			return (f(done) / f(expected)) * 100;
		}
	};
	$: if (task.nix_status) {
		progress = progressScalingFunction(task.nix_status.done, task.nix_status.expected);
	}
</script>

<div class="flex gap-2 mr-2 items-center">
	{#if task.state === 'pending'}
		<PendingIcon size="18" />
		{$t('taskbar.pending')}
	{:else if task.state === 'running'}
		<RunningIcon size="18" />
		{$t('taskbar.running')}
	{:else if task.state === 'completed'}
		<CompletedIcon size="18" />
		{$t('taskbar.completed')}
	{:else if task.state === 'failed'}
		<FailedIcon size="18" />
		{$t('taskbar.failed')}
	{:else}
		{task.state}
	{/if}
</div>
{#if task.nix_status && task.state === 'running'}
	<Progressbar {progress} />
{/if}
