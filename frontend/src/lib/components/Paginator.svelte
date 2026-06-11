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
		<ChevronLeft class="h-4" />
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
		<ChevronRight class="h-4" />
	</button>
</div>

<style lang="postcss">
	.paginate {
		gap: 4px;
	}
	.page-button {
		border: 1px solid var(--ds-border);
		background: var(--ds-surface-2);
		color: var(--ds-text-dim);
		border-radius: 7px;
		padding: 0;
		height: 1.75rem;
		min-width: 1.75rem;
		font-size: 12.5px;
		font-weight: 500;
		display: flex;
		justify-content: center;
		align-items: center;
		transition:
			background 0.12s,
			border-color 0.12s,
			color 0.12s;
	}
	.page-button:hover {
		background: var(--ds-surface-3);
		border-color: var(--ds-border-strong);
		color: var(--ds-text);
	}
	.page-button.active {
		background: var(--ds-accent);
		border-color: var(--ds-accent);
		color: #fff;
	}
</style>
