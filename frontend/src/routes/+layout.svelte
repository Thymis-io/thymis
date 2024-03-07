<script lang="ts">
	import '../app.postcss';
	import Navbar from './Navbar.svelte';
	import Sidebar from './Sidebar.svelte';
	import type { PageData } from '../routes/$types';

	export let data: PageData;
</script>

<header
	class="sticky top-0 z-40 mx-auto w-full flex-none border-b border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800"
>
	<Navbar />
</header>
<div class="overflow-hidden lg:flex">
	<Sidebar {data} />
	<div class="relative h-full w-full overflow-y-auto lg:ml-64 p-4">
		<slot />
	</div>
</div>
