<script lang="ts">
	import Sidebar from '$lib/sidebar/Sidebar.svelte';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';

	export let drawerHidden = false;
</script>

<SplitPane
	class="!block lg:!grid"
	type="horizontal"
	pos="16rem"
	min="10rem"
	max="64rem"
	priority="min"
	leftPaneClass="!hidden lg:!block"
	dividerClass="!hidden lg:!block"
>
	<Sidebar slot="a" bind:drawerHidden />
	<div class="p-4 bg-gray-50 dark:bg-gray-900 !overflow-y-scroll" slot="b">
		<slot />
	</div>
</SplitPane>
