<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort, cancelTask, retryTask } from '$lib/taskstatus';
	import { page } from '$app/stores';
	import { Button } from 'flowbite-svelte';
	export let task: TaskShort;
</script>

<div class="flex flex-row items-center justify-center space-x-2">
	{#if task.state === 'pending'}
		<Button class="px-4 py-2 whitespace-nowrap" on:click={() => cancelTask(task.id)}>
			{$t('taskbar.cancel')}
		</Button>
	{:else if task.state === 'running'}
		<Button class="px-4 py-2 whitespace-nowrap" on:click={() => cancelTask(task.id)}>
			{$t('taskbar.cancel')}
		</Button>
	{:else if task.state === 'completed'}
		<Button class="px-4 py-2 whitespace-nowrap" on:click={() => retryTask(task.id)}>
			{$t('taskbar.retry')}
		</Button>
	{:else if task.state === 'failed'}
		<Button class="px-4 py-2 whitespace-nowrap" on:click={() => retryTask(task.id)}>
			{$t('taskbar.retry')}
		</Button>
	{/if}
	<a data-sveltekit-preload-data="tap" href="/tasks/{task.id}{$page.url.search}">
		<Button class="px-4 py-2 whitespace-nowrap">
			{$t('taskbar.details')}
		</Button>
	</a>
</div>
