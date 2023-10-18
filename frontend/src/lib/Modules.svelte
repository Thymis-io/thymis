<script>
	import ModuleCard from './ModuleCard.svelte';
	import { modules } from './modules';
	let searchInput = '';
</script>

<div>
	<div class="columns-3 mb-10">
		<input bind:value={searchInput} class="input" type="text" placeholder="Search..." />
	</div>
	<div class="snap-x scroll-px-4 snap-mandatory scroll-smooth flex gap-4 overflow-x-auto py-10">
		{#each modules as module}
			<ModuleCard {...module} />
		{/each}
	</div>
</div>
