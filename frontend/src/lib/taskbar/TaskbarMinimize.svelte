<script lang="ts">
	import ChevronsDown from 'lucide-svelte/icons/chevrons-down';
	import ChevronsUp from 'lucide-svelte/icons/chevrons-up';

	interface Props {
		class?: string;
		taskbarMinimized?: boolean;
	}

	let { class: className = '', taskbarMinimized = $bindable(false) }: Props = $props();
</script>

<div class={'absolute right-0 z-10 ' + className}>
	<button
		class="float-right px-2 hover:bg-gray-200 dark:hover:bg-gray-600"
		onclick={() => (taskbarMinimized = !taskbarMinimized)}
	>
		{#if taskbarMinimized}
			<ChevronsUp size={22} />
		{:else}
			<ChevronsDown size={22} />
		{/if}
	</button>
</div>
