<script lang="ts">
	import { run } from 'svelte/legacy';

	import '../../app.css';
	import { t } from 'svelte-i18n';
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
		if (!taskbarMinimized && convertLengthToPixels(pos) < convertLengthToPixels('80px')) {
			taskbarMinimized = true;
		}
		if (taskbarMinimized && convertLengthToPixels(pos) > convertLengthToPixels('80px')) {
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
		startNotificationSocket(data.globalState);
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

<ProgressBar color="var(--ds-accent)" zIndex={100} />

<div class="ds-shell">
	<Sidebar globalState={data.globalState} user={data.user} bind:drawerHidden />

	{#if !drawerHidden}
		<button
			class="ds-backdrop lg:hidden"
			aria-label={$t('common.close-navigation')}
			onclick={() => (drawerHidden = true)}
		></button>
	{/if}

	<div class="ds-main">
		<Navbar globalState={data.globalState} nav={data.nav} bind:drawerHidden />

		<div class="ds-body">
			<SplitPane
				type="vertical"
				reverse={true}
				pos={taskbarMinimized ? '38px' : '30%'}
				min={taskbarMinimized ? '38px' : '12rem'}
				max={taskbarMinimized ? '38px' : '80%'}
				onchange={onSplitpaneChange}
			>
				{#snippet a()}
					<MainWindow globalState={data.globalState}>
						{@render children?.()}
					</MainWindow>
				{/snippet}
				{#snippet b()}
					<div class="flex flex-col">
						{#if !taskbarMinimized}
							<div
								id="taskbar"
								class="flex-1 overflow-y-auto overflow-x-hidden border-t bg-[var(--ds-surface)] border-[var(--ds-border)]"
							>
								<Taskbar globalState={data.globalState} bind:taskbarMinimized />
							</div>
						{/if}
						<div class="relative h-[38px]">
							<TaskbarMinimize bind:taskbarMinimized class="top-0 h-full" />
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
		--navbar-height: 52px;
	}

	.ds-shell {
		display: flex;
		height: 100vh;
		width: 100%;
		overflow: hidden;
		background: var(--ds-bg);
		color: var(--ds-text);
	}
	.ds-main {
		display: flex;
		flex-direction: column;
		flex: 1;
		min-width: 0;
		overflow: hidden;
	}
	.ds-body {
		flex: 1;
		min-height: 0;
	}
	.ds-backdrop {
		position: fixed;
		inset: 0;
		z-index: 55;
		background: rgba(0, 0, 0, 0.45);
		border: none;
	}
</style>
