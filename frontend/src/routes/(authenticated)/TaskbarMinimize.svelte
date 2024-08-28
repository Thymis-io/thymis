<script lang="ts">
	import ChevronsDown from 'lucide-svelte/icons/chevrons-down';
	import ChevronsUp from 'lucide-svelte/icons/chevrons-up';

	export let taskBarMinimized = false;
</script>

<div class="h-8 z-10 absolute right-0">
	<button
		class="float-right px-2 hover:bg-gray-200 dark:hover:bg-gray-600"
		on:click={() => (taskBarMinimized = !taskBarMinimized)}
	>
		{#if taskBarMinimized}
			<ChevronsUp size={22} />
		{:else}
			<ChevronsDown size={22} />
		{/if}
	</button>
</div>
