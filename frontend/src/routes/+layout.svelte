<script lang="ts">
	import '../app.postcss';
	import Navbar from './Navbar.svelte';
	import Sidebar from './Sidebar.svelte';
	import type { LayoutData } from '../routes/$types';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';

	export let data: LayoutData;

	let drawerHidden = true;
</script>

<header
	class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
>
	<Navbar bind:drawerHidden />
</header>
<SplitPane type="horizontal" pos="50%">
	<Sidebar slot="a" bind:drawerHidden bind:state={data.state} />
	<div slot="b" class="">
		<slot />
	</div>
</SplitPane>
