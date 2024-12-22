<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort, cancelTask, retryTask, runImmediately } from '$lib/taskstatus';
	import { page } from '$app/stores';
	import { Button } from 'flowbite-svelte';
	export let task: TaskShort;
</script>

<div class="flex flex-row items-center space-x-2">
	{#if task.state === 'pending'}
		<Button
			class="btn btn-sm btn-danger px-4 py-2 whitespace-nowrap"
			on:click={() => cancelTask(task.id)}
		>
			{$t('taskbar.cancel')}
		</Button>
		<Button
			class="btn btn-sm btn-primary px-4 py-2 whitespace-nowrap"
			on:click={() => runImmediately(task.id)}
		>
			{$t('taskbar.run-immediately')}
		</Button>
	{:else if task.state === 'running'}
		<Button
			class="btn btn-sm btn-danger px-4 py-2 whitespace-nowrap"
			on:click={() => cancelTask(task.id)}
		>
			{$t('taskbar.cancel')}
		</Button>
	{:else if task.state === 'completed'}
		<Button
			class="btn btn-sm btn-primary px-4 py-2 whitespace-nowrap"
			on:click={() => retryTask(task.id)}
		>
			{$t('taskbar.retry')}
		</Button>
	{:else if task.state === 'failed'}
		<Button
			class="btn btn-sm btn-primary px-4 py-2 whitespace-nowrap"
			on:click={() => retryTask(task.id)}
		>
			{$t('taskbar.retry')}
		</Button>
	{/if}
	<a data-sveltekit-preload-data="tap" href="/tasks/{task.id}{$page.url.search}">
		<Button class="btn btn-sm btn-primary px-4 py-2 whitespace-nowrap">
			{$t('taskbar.details')}
		</Button>
	</a>
</div>
