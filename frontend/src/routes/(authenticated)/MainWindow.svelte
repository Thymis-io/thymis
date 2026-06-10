<script lang="ts">
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		drawerHidden?: boolean;
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="w-full h-full overflow-y-auto p-4 bg-[var(--ds-bg)] text-[var(--ds-text)]">
	{@render children?.()}
</div>
