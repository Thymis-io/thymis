<script lang="ts">
	import { run } from 'svelte/legacy';

	import '../../app.postcss';
	import Navbar from '$lib/navbar/Navbar.svelte';
	import Sidebar from '$lib/sidebar/Sidebar.svelte';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';
	import type { LayoutData } from './$types';
	import { taskStatus } from '$lib/taskstatus';
	import Taskbar from '$lib/taskbar/Taskbar.svelte';
	import MainWindow from './MainWindow.svelte';
	import TaskbarMinimize from '$lib/taskbar/TaskbarMinimize.svelte';
	import TaskbarSmall from '$lib/taskbar/TaskbarSmall.svelte';
	import { browser } from '$app/environment';
	import { SvelteToast } from '@zerodevx/svelte-toast';
	import { onMount } from 'svelte';
	import { startNotificationSocket } from '$lib/notification';

	import { ProgressBar } from '@prgm/sveltekit-progress-bar';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let taskbarMinimized = $state(data.minimizeTaskbar ?? false);

	run(() => {
		if (browser) {
			document.cookie = `taskbar-minimized=${taskbarMinimized}; SameSite=Lax;`;
		}
	});

	run(() => {
		let taskStatusValue = {};
		for (const task of data.allTasks) {
			taskStatusValue[task.id] = task;
		}
		$taskStatus = taskStatusValue;
	});

	let drawerHidden = $state(true);

	onMount(() => {
		startNotificationSocket();
	});
</script>

<svelte:head>
	<title>Thymis Dashboard</title>
</svelte:head>

<ProgressBar class="text-primary-500" zIndex={100} />

<div class="contents bg-gray-50 dark:bg-gray-900 dark:text-white">
	<header
		class="fixed top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
	>
		<Navbar
			globalState={data.globalState}
			nav={data.nav}
			class="h-[calc(var(--navbar-height))] max-h-[calc(var(--navbar-height))]"
			bind:drawerHidden
		/>
	</header>
	<div class="h-screen block z-50 {drawerHidden ? 'hidden' : ''} lg:hidden">
		<Sidebar
			globalState={data.globalState}
			asideClass="h-full pt-[calc(var(--navbar-height))]"
			bind:drawerHidden
		/>
	</div>
	<div class="{drawerHidden ? '' : 'hidden'} lg:block pt-[calc(var(--navbar-height))] h-full">
		<div class="flex flex-row h-full">
			{#if taskbarMinimized}
				<div class="w-full relative dark:border-gray-600 bg-gray-50 dark:bg-gray-900 mb-[40px]">
					<MainWindow globalState={data.globalState} bind:drawerHidden>
						{@render children?.()}
					</MainWindow>
					<div class="relative h-[40px]">
						<TaskbarMinimize bind:taskbarMinimized class="mt-2" />
						<TaskbarSmall globalState={data.globalState} inPlaywright={data.inPlaywright} />
					</div>
				</div>
			{:else}
				<SplitPane type="vertical" pos="70%" min="12rem" max="80%">
					{#snippet a()}
						<MainWindow globalState={data.globalState} bind:drawerHidden>
							{@render children?.()}
						</MainWindow>
					{/snippet}
					{#snippet b()}
						<div
							id="taskbar"
							class="w-full relative border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
						>
							<div class="max-h-full overflow-x-hidden overflow-y-auto h-[calc(100%-40px)]">
								<Taskbar globalState={data.globalState} bind:taskbarMinimized />
							</div>
							<div class="w-full h-[40px]">
								<TaskbarMinimize bind:taskbarMinimized class="mt-2" />
								<TaskbarSmall globalState={data.globalState} inPlaywright={data.inPlaywright} />
							</div>
						</div>
					{/snippet}
				</SplitPane>
			{/if}
		</div>
	</div>
</div>
<SvelteToast
	options={{
		duration: 0,
		initial: 0,
		next: 0,
		classes: ['whitespace-pre-line [overflow-wrap:anywhere]'],
		theme: { '--toastWidth': '40rem' }
	}}
/>

<style lang="postcss">
	:root {
		--navbar-height: 50px;
	}
</style>
