<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort } from '$lib/taskstatus';
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

	const pillClass = $derived(
		task.state === 'pending'
			? 'warning'
			: task.state === 'running'
				? 'info'
				: task.state === 'completed'
					? 'online'
					: task.state === 'failed'
						? 'danger'
						: 'offline'
	);

	let progress = $state(0);
	const progressScalingFunction = (done: number, expected: number) => {
		const f = (x: number) => x * x + 1;
		// if both are 0, progress is 0
		if (done === 0 || expected === 0) {
			return 0;
		} else {
			return Math.min(1, f(done) / f(expected)) * 100;
		}
	};
	$effect(() => {
		if (task.nix_status) {
			progress = progressScalingFunction(task.nix_status.done, task.nix_status.expected);
		}
	});
</script>

<div class="ds-status-pill {pillClass}">
	{#if task.state === 'pending'}
		{#if showIcons}
			<PendingIcon size="14" />
		{/if}
		{#if showText}
			{$t('taskbar.pending')}
		{/if}
	{:else if task.state === 'running'}
		{#if showIcons}
			<RunningIcon size="14" />
		{/if}
		{#if showText}
			{$t('taskbar.running')}
		{/if}
	{:else if task.state === 'completed'}
		{#if showIcons}
			<CompletedIcon size="14" />
		{/if}
		{#if showText}
			{$t('taskbar.completed')}
		{/if}
	{:else if task.state === 'failed'}
		{#if showIcons}
			<FailedIcon size="14" />
		{/if}
		{#if showText}
			{$t('taskbar.failed')}
		{/if}
	{:else}
		{task.state}
	{/if}
</div>
{#if showProgress && task.nix_status && task.state === 'running'}
	<div class="ds-progress mt-1.5" aria-hidden="true">
		<span style="width: {progress}%"></span>
	</div>
{/if}

<style lang="postcss">
	.ds-progress {
		width: 100%;
		height: 6px;
		border-radius: 999px;
		background: var(--ds-surface-2);
		overflow: hidden;
	}
	.ds-progress span {
		display: block;
		height: 100%;
		border-radius: 999px;
		background: var(--ds-accent);
		transition: width 0.3s ease;
	}
</style>
