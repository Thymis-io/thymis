<script lang="ts">
	import { type Task } from '$lib/taskstatus';
	export let task: Task;
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
</script>

{task.state}

{#if task.nix_status && task.state === 'running'}
	<Progressbar {progress} />
{/if}
