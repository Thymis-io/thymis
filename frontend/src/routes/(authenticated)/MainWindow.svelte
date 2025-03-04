<script lang="ts">
	import Sidebar from '$lib/sidebar/Sidebar.svelte';

	interface Props {
		drawerHidden?: boolean;
		children?: import('svelte').Snippet;
	}

	let { drawerHidden = $bindable(false), children }: Props = $props();
</script>

<div class="grid lg:grid-cols-[6rem_1fr] w-full h-full overflow-y-auto">
	<Sidebar bind:drawerHidden />
	<div class="p-4 bg-gray-50 dark:bg-gray-900 !overflow-y-auto">
		{@render children?.()}
	</div>
</div>
