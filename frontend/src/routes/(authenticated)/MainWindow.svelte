<script lang="ts">
	import Sidebar from '$lib/sidebar/Sidebar.svelte';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		drawerHidden?: boolean;
		children?: import('svelte').Snippet;
	}

	let { globalState, drawerHidden = $bindable(false), children }: Props = $props();
</script>

<div class="grid lg:grid-cols-[6rem_1fr] w-full h-full overflow-y-auto">
	<Sidebar {globalState} bind:drawerHidden />
	<div class="p-4 bg-gray-50 dark:bg-gray-900 !overflow-y-auto">
		{@render children?.()}
	</div>
</div>
