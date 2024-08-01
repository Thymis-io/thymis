<script lang="ts">
	import '../app.postcss';
	import Navbar from '../lib/navbar/Navbar.svelte';
	import Sidebar from '../lib/sidebar/Sidebar.svelte';
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

	let drawerHidden = true;
</script>

<div class="bg-gray-50 dark:bg-gray-900">
	<header
		class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
	>
		<Navbar bind:drawerHidden />
	</header>
	<div class="overflow-hidden lg:flex">
		<Sidebar bind:drawerHidden />
		<div class="relative h-full w-full overflow-y-auto lg:ml-64 p-4">
			<slot />
		</div>
	</div>
</div>
