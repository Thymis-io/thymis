<script lang="ts">
	import '../app.postcss';
	import Navbar from '$lib/navbar/Navbar.svelte';
	import Sidebar from '$lib/sidebar/Sidebar.svelte';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';
	import type { LayoutData } from '../routes/$types';
	import { saveState } from '$lib/state';
	import { state } from '$lib/state';

	export let data: LayoutData;

	$state = data.state;
	let lastDataState = data.state;
	let lastState = data.state;

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
		<SplitPane type="vertical" pos="60%" min="12rem" max="80%">
			<SplitPane
				class="!block lg:!grid"
				type="horizontal"
				pos="16rem"
				min="16rem"
				max="64rem"
				priority="min"
				leftPaneClass="!hidden lg:!block"
				slot="a"
			>
				<Sidebar slot="a" bind:drawerHidden />
				<div class="p-4 bg-gray-50 dark:bg-gray-900 !overlflow-y-scroll" slot="b">
					<slot />
				</div>
			</SplitPane>
			<div class="border dark:border-gray-600 bg-gray-50 dark:bg-gray-900" slot="b">
				Hello I'm task
			</div>
		</SplitPane>
	</div>
</div>

<style>
	:root {
		--navbar-height: 4rem;
	}
</style>
