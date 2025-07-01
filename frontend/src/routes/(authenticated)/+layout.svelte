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
	import { beforeNavigate } from '$app/navigation';
	import type { Length } from '$lib/splitpane/types';

	interface Props {
		data: LayoutData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	let taskbarMinimized = $state(data.minimizeTaskbar ?? false);

	const convertLengthToPixels = (rem: string) => {
		if (rem.endsWith('rem')) {
			const remValue = parseFloat(rem.slice(0, -3));
			return remValue * parseFloat(getComputedStyle(document.documentElement).fontSize);
		} else if (rem.endsWith('%')) {
			const percentageValue = parseFloat(rem.slice(0, -1));
			const parentHeight = document.documentElement.clientHeight;
			return (percentageValue / 100) * parentHeight;
		} else if (rem.endsWith('px')) {
			return parseFloat(rem.slice(0, -2));
		}
		return parseFloat(rem);
	};

	const onSplitpaneChange = (pos: Length) => {
		if (!taskbarMinimized && convertLengthToPixels(pos) < convertLengthToPixels('50px')) {
			taskbarMinimized = true;
		}
		if (taskbarMinimized && convertLengthToPixels(pos) > convertLengthToPixels('50px')) {
			taskbarMinimized = false;
		}
	};

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

	beforeNavigate((navigation) => {
		navigation.complete.catch((reason) => {
			// log reason
			console.error('Navigation failed:', reason);
		});
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
			<SplitPane
				type="vertical"
				reverse={true}
				pos={taskbarMinimized ? '40px' : '30%'}
				min={taskbarMinimized ? '40px' : '12rem'}
				max={taskbarMinimized ? '40px' : '80%'}
				onchange={onSplitpaneChange}
			>
				{#snippet a()}
					<MainWindow globalState={data.globalState} bind:drawerHidden>
						{@render children?.()}
					</MainWindow>
				{/snippet}
				{#snippet b()}
					<div class="flex flex-col">
						{#if !taskbarMinimized}
							<div
								id="taskbar"
								class="flex-1 overflow-y-auto border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-900"
							>
								<Taskbar globalState={data.globalState} bind:taskbarMinimized />
							</div>
						{/if}
						<div class="h-[40px]">
							<TaskbarMinimize bind:taskbarMinimized class="mt-2" />
							<TaskbarSmall globalState={data.globalState} inPlaywright={data.inPlaywright} />
						</div>
					</div>
				{/snippet}
			</SplitPane>
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
