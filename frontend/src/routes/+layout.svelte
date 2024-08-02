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

<div class="bg-gray-50 dark:bg-gray-900">
	<header
		class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
	>
		<Navbar bind:drawerHidden />
	</header>
	<div class="contents lg:hidden">
		<Sidebar bind:drawerHidden />
	</div>
	<SplitPane type="vertical" pos="64rem" min="16rem" max="64rem">
		<SplitPane
			class="sticky top-0 !block lg:!grid"
			type="horizontal"
			pos="16rem"
			min="16rem"
			max="64rem"
			priority="min"
			leftPaneClass="!hidden lg:!block"
			slot="a"
		>
			<div slot="a" class="sticky top-0">
				<Sidebar bind:drawerHidden />
			</div>
			<div slot="b" class="p-4 !overflow-y-scroll !h-[calc(100vh-4.6rem)]">
				<slot />
			</div>
			<!-- </div> -->
		</SplitPane>
		<div slot="b">Hello I'm task</div>
	</SplitPane>
</div>
