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
	import TaskbarMinimize from './TaskbarMinimize.svelte';

	export let data: LayoutData;

	$state = data.state;
	let lastDataState = data.state;
	let lastState = data.state;

	let taskBarMinimized = false;

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

	$: $taskStatus = data.allTasks;

	let drawerHidden = false;
</script>

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
			{#if taskBarMinimized}
				<div class="w-full relative grid grid-cols-1 grid-rows-[calc(100%-40px)_40px]">
					<MainWindow bind:drawerHidden><slot /></MainWindow>
					<div class="relative bg-gray-50 dark:bg-gray-700">
						<TaskbarMinimize bind:taskBarMinimized />
					</div>
				</div>
			{:else}
				<SplitPane type="vertical" pos="60%" min="12rem" max="80%">
					<MainWindow slot="a" bind:drawerHidden>
						<slot />
					</MainWindow>
					<div
						class="w-full relative border dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
						slot="b"
					>
						<TaskbarMinimize bind:taskBarMinimized />
						<Taskbar />
					</div>
				</SplitPane>
			{/if}
		</div>
	</div>
</div>

<style>
	:root {
		--navbar-height: 4rem;
	}
</style>
