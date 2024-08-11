<script lang="ts">
	import { type Task, cancelTask, retryTask, runImmediately } from '$lib/taskstatus';
	import { Button } from 'flowbite-svelte';
	export let task: Task;
</script>

<div class="flex flex-row items-center space-x-2">
	{#if task.state === 'pending'}
		<Button class="btn btn-sm btn-danger" on:click={() => cancelTask(task.id)}>Cancel</Button>
		<Button class="btn btn-sm btn-primary" on:click={() => runImmediately(task.id)}
			>Run Immediately</Button
		>
	{:else if task.state === 'running'}
		<Button class="btn btn-sm btn-danger" on:click={() => cancelTask(task.id)}>Cancel</Button>
	{:else if task.state === 'completed'}
		<Button class="btn btn-sm btn-primary" on:click={() => retryTask(task.id)}>Retry</Button>
	{:else if task.state === 'failed'}
		<Button class="btn btn-sm btn-primary" on:click={() => retryTask(task.id)}>Retry</Button>
	{/if}
	<a href="/tasks/{task.id}"><Button class="btn btn-sm btn-primary">View</Button></a>
</div>
