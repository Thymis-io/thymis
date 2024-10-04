<script lang="ts">
	import { type NixCommandTask, type Task } from '$lib/taskstatus';
	export let task: Task;
	import { Progressbar } from 'flowbite-svelte';

	// $: isNixTask = task.type === 'nixcommandtask';
	const isNixTask = (task: Task): task is NixCommandTask => task.type === 'nixcommandtask';
	// progress bar in task.data.nix_process.global_done and global_expected

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
	$: if (isNixTask(task)) {
		// if both are 0, progress is 0
		// if (task.status.done === 0) {
		// 	progress = 0;
		// } else {
		// 	progress = (task.status.done / task.status.expected) * 100;
		// }
		progress = progressScalingFunction(task.status.done, task.status.expected);
	}
</script>

{task.state}

{#if isNixTask(task) && task.state === 'running'}
	<Progressbar {progress} />
{/if}
