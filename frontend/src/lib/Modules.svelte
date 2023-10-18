<script>
	import ModuleCard from './ModuleCard.svelte';
	let searchInput = '';
</script>

<div>
	<div class="columns-3 mb-16">
		<input bind:value={searchInput} class="input" type="text" />
	</div>
	<div
		class="snap-x scroll-px-4 snap-mandatory scroll-smooth flex gap-4 overflow-x-auto px-4 py-10"
	>
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
		<ModuleCard />
	</div>
</div>
