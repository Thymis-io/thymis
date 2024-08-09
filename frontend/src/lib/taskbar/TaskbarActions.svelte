<script lang="ts">
	import { taskStatus, type Task, type CommandTask, type CompositeTask } from '$lib/taskstatus';
	import { Button } from 'flowbite-svelte';
	export let task: Task;
	// 3 actions: cancel, retry, view detail page
	export let taskIdx: number;
</script>

<div class="flex flex-row items-center space-x-2">
	{#if task.state === 'pending'}
		<Button class="btn btn-sm btn-primary">Cancel</Button>
	{/if}
	{#if task.state === 'failed'}
		<Button class="btn btn-sm btn-primary">Retry</Button>
	{/if}
	<a href="/tasks/{taskIdx}"><Button class="btn btn-sm btn-primary">View</Button></a>
</div>
