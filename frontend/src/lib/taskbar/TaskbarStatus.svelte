<script lang="ts">
	import { type Task } from '$lib/taskstatus';
	export let task: Task;
	import { Progressbar } from 'flowbite-svelte';

	$: isNixTask = 'nix_process' in task.data;
	// progress bar in task.data.nix_process.global_done and global_expected

	let progress = 0;
	$: if (isNixTask) {
		progress = (task.data.nix_process.global_done / task.data.nix_process.global_expected) * 100;
	}
</script>

{task.state}

{#if isNixTask && task.state === 'running'}
	<Progressbar {progress} />
{/if}
