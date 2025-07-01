<script lang="ts">
	import ChevronLeft from 'lucide-svelte/icons/chevron-left';
	import ChevronRight from 'lucide-svelte/icons/chevron-right';

	interface Props {
		totalCount: number;
		pageSize: number;
		limit?: number;
		page: number;
		onChange: (page: number) => void;
	}

	let { totalCount, pageSize, limit = 2, page, onChange }: Props = $props();

	let pageCount = $derived(Math.max(Math.ceil(totalCount / pageSize), 1));
	let visiblePagesCount = $derived(limit * 2 + 1);
	let visiblePagesStart = $derived(
		Math.max(Math.min(page - limit - 1, pageCount - visiblePagesCount), 0)
	);
	let visiblePages = $derived(
		Array.from({ length: pageCount }, (_, i) => i).slice(
			visiblePagesStart,
			visiblePagesStart + visiblePagesCount
		)
	);

	const handlePageChange = (page: number) => {
		if (page < 1 || page > pageCount) return;
		onChange(page);
	};
</script>

<div class="flex items-center paginate">
	<button onclick={() => handlePageChange(page - 1)} class="page-button">
		<ChevronLeft class="h-6" />
	</button>
	{#each visiblePages as i}
		<button
			onclick={() => handlePageChange(i + 1)}
			class="page-button"
			class:active={i + 1 === page}
		>
			{i + 1}
		</button>
	{/each}
	<button onclick={() => handlePageChange(page + 1)} class="page-button">
		<ChevronRight class="h-6" />
	</button>
</div>

<style lang="postcss">
	.page-button {
		border: 1px solid rgb(128, 128, 128);
		padding: 0.1rem;
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
</style>
