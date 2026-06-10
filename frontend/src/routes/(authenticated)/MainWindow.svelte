<script lang="ts">
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		drawerHidden?: boolean;
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<!-- Outer div is the SplitPane's direct child (forced overflow:hidden, h-full);
     the inner div is the actual scroll container. -->
<div class="w-full h-full bg-[var(--ds-bg)] text-[var(--ds-text)]">
	<div class="w-full h-full overflow-y-auto p-4">
		{@render children?.()}
	</div>
</div>
