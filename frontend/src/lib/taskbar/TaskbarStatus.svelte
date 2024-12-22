<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort } from '$lib/taskstatus';
	export let task: TaskShort;
	import { Progressbar } from 'flowbite-svelte';

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

	const taskState = {
		pending: $t('taskbar.pending'),
		running: $t('taskbar.running'),
		completed: $t('taskbar.completed'),
		failed: $t('taskbar.failed')
	};
</script>

{task.state in taskState ? taskState[task.state] : task.state}

{#if task.nix_status && task.state === 'running'}
	<Progressbar {progress} />
{/if}
