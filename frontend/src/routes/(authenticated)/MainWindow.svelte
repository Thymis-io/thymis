<script lang="ts">
	import Sidebar from '$lib/sidebar/Sidebar.svelte';

	export let drawerHidden = false;
</script>

<div class="grid lg:grid-cols-[6rem_1fr] w-full h-full overflow-y-auto">
	<Sidebar bind:drawerHidden />
	<div class="p-4 bg-gray-50 dark:bg-gray-900 !overflow-y-auto">
		<slot />
	</div>
</div>
