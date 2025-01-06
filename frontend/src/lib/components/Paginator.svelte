<script lang="ts">
	import ChevronLeft from 'lucide-svelte/icons/chevron-left';
	import ChevronRight from 'lucide-svelte/icons/chevron-right';

	export let totalCount: number;
	export let pageSize: number;
	export let limit: number = 2;
	export let page: number;
	export let onChange: (page: number) => void;

	$: pageCount = Math.ceil(totalCount / pageSize);
	$: visiblePagesCount = limit * 2 + 1;
	$: visiblePagesStart = Math.max(Math.min(page - limit - 1, pageCount - visiblePagesCount), 0);
	$: visiblePages = Array.from({ length: pageCount }, (_, i) => i).slice(
		visiblePagesStart,
		visiblePagesStart + visiblePagesCount
	);

	const handlePageChange = (page: number) => {
		if (page < 1 || page > pageCount) return;
		onChange(page);
	};
</script>

<div class="flex items-center paginate">
	<button on:click={() => handlePageChange(page - 1)} class="page-button">
		<ChevronLeft class="h-6" />
	</button>
	{#each visiblePages as i}
		<button
			on:click={() => handlePageChange(i + 1)}
			class={'page-button'}
			class:active={i + 1 === page}
		>
			{i + 1}
		</button>
	{/each}
	<button on:click={() => handlePageChange(page + 1)} class="page-button">
		<ChevronRight class="h-6" />
	</button>
</div>

<style lang="postcss">
	.page-button {
		border: 1px solid rgb(128, 128, 128);
		padding: 0.1rem;
		min-width: 1.5rem;
		height: 1.6rem;
		width: 1.6rem;
		display: flex;
		justify-content: center;
		align-items: center;
	}
	.paginate :first-child {
		border-radius: 0.3rem 0 0 0.3rem;
	}
	.paginate :last-child {
		border-radius: 0 0.3rem 0.3rem 0;
	}
	.page-button.active {
		@apply bg-gray-300;
		@apply text-primary-500;
	}
	.page-button.active:is(.dark *) {
		@apply bg-gray-500;
	}
	.page-button:hover {
		@apply bg-gray-300;
	}
	.page-button:hover:is(.dark *) {
		@apply bg-gray-500;
	}
</style>
