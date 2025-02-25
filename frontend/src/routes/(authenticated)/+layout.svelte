<script lang="ts">
	import '../../app.postcss';
	import Navbar from '$lib/navbar/Navbar.svelte';
	import Sidebar from '$lib/sidebar/Sidebar.svelte';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';
	import type { LayoutData } from './$types';
	import { saveState } from '$lib/state';
	import { state } from '$lib/state';
	import { taskStatus } from '$lib/taskstatus';
	import Taskbar from '$lib/taskbar/Taskbar.svelte';
	import MainWindow from './MainWindow.svelte';
	import TaskbarMinimize from '$lib/taskbar/TaskbarMinimize.svelte';
	import TaskbarSmall from '$lib/taskbar/TaskbarSmall.svelte';
	import { browser } from '$app/environment';
	import { SvelteToast } from '@zerodevx/svelte-toast';
	import { onMount } from 'svelte';
	import { startNotificationSocket } from '$lib/notification';

	export let data: LayoutData;

	$state = data.state;
	let lastDataState = data.state;
	let lastState = data.state;

	let taskbarMinimized = data.minimizeTaskbar ?? false;

	$: {
		if (browser) {
			document.cookie = `taskbar-minimized=${taskbarMinimized}; SameSite=Lax;`;
		}
	}

	$: {
		// check which state changed
		if (lastDataState !== data.state && lastState !== $state) {
			// unexpected state change
			console.error('Unexpected state change');
			console.log(lastDataState, lastState, data.state);
		} else if (lastDataState !== data.state) {
			// server state changed
			$state = data.state; // update local state store
		} else if (lastState !== $state) {
			// local state changed
			saveState(); // save local state to server
		}
		lastDataState = data.state;
		lastState = $state;
	}

	$: {
		let taskStatusValue = {};
		for (const task of data.allTasks) {
			taskStatusValue[task.id] = task;
		}
		$taskStatus = taskStatusValue;
	}

	let drawerHidden = true;

	onMount(() => {
		startNotificationSocket();
	});
</script>

<svelte:head>
	<title>Thymis Dashboard</title>
</svelte:head>

<div class="contents bg-gray-50 dark:bg-gray-900 dark:text-white">
	<header
		class="fixed top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
	>
		<Navbar
			class="h-[calc(var(--navbar-height))] max-h-[calc(var(--navbar-height))]"
			bind:drawerHidden
		/>
	</header>
	<div class="h-screen block z-50 {drawerHidden ? 'hidden' : ''} lg:hidden">
		<Sidebar asideClass="h-full pt-[calc(var(--navbar-height))]" bind:drawerHidden />
	</div>
	<div class="{drawerHidden ? '' : 'hidden'} lg:block pt-[calc(var(--navbar-height))] h-full">
		<div class="flex flex-row h-full">
			{#if taskbarMinimized}
				<div class="w-full relative dark:border-gray-600 bg-gray-50 dark:bg-gray-900 mb-[40px]">
					<MainWindow bind:drawerHidden><slot /></MainWindow>
					<div class="relative h-[40px]">
						<TaskbarMinimize bind:taskbarMinimized class="mt-2" />
						<TaskbarSmall inPlaywright={data.inPlaywright} />
					</div>
				</div>
			{:else}
				<SplitPane type="vertical" pos="70%" min="12rem" max="80%">
					<MainWindow bind:drawerHidden slot="a">
						<slot />
					</MainWindow>
					<div
						class="w-full relative border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
						slot="b"
					>
						<div class="max-h-full overflow-x-hidden overflow-y-auto h-[calc(100%-40px)]">
							<Taskbar bind:taskbarMinimized />
						</div>
						<div class="w-full h-[40px]">
							<TaskbarMinimize bind:taskbarMinimized class="mt-2" />
							<TaskbarSmall inPlaywright={data.inPlaywright} />
						</div>
					</div>
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
		classes: ['whitespace-pre-line'],
		theme: { '--toastWidth': '32rem' }
	}}
/>

<style lang="postcss">
	:root {
		--navbar-height: 50px;
	}
	:global(div.multiselect) {
		@apply !p-2;
		@apply !rounded-lg;
		@apply !bg-gray-50;
		@apply dark:!bg-gray-600;
		@apply !border;
		@apply !border-gray-300;
		@apply dark:!border-gray-500;
	}
	:global(div.multiselect.open) {
		@apply !border-primary-500;
		@apply !ring-primary-500;
		@apply dark:focus:!border-primary-500;
		@apply dark:focus:!ring-primary-500;
	}
	:global(div.multiselect > svg) {
		width: 18px;
	}
	:global(div.multiselect > ul.options > li) {
		@apply bg-gray-100;
		@apply dark:bg-gray-800;
	}
	:global(div.multiselect > ul.options > li.active) {
		@apply bg-gray-200;
		@apply dark:bg-gray-700;
	}
	:global(div.multiselect > ul > input) {
		--tw-ring-shadow: none;
	}
	:global(div.multiselect > ul.selected > li) {
		@apply !p-1;
		@apply !px-2;
		@apply !m-[1px];
		@apply !rounded-lg;
	}
</style>
