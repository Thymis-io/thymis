<script lang="ts">
	import { t } from 'svelte-i18n';
	import { browser } from '$app/environment';

	interface Props {
		cookieKey: string;
		value: number;
	}

	let { cookieKey, value = $bindable() }: Props = $props();

	const COLUMN_OPTIONS = [1, 2, 3, 4, 5, 6];

	const setColumns = (v: number) => {
		value = v;
		if (browser) document.cookie = `${cookieKey}=${v}; SameSite=Lax;`;
	};
</script>

<span class="cols-label">{$t('vnc.column-count')}</span>
<div class="cols-seg" role="group" aria-label={$t('vnc.column-count')}>
	{#each COLUMN_OPTIONS as v (v)}
		<button
			type="button"
			class="cols-seg-btn"
			class:active={value === v}
			aria-pressed={value === v}
			onclick={() => setColumns(v)}>{v}</button
		>
	{/each}
</div>

<style lang="postcss">
	.cols-label {
		color: var(--ds-text-dim);
		font-size: 13px;
	}
	/* segmented control for choosing how many displays per row */
	.cols-seg {
		display: inline-flex;
		padding: 2px;
		gap: 2px;
		border-radius: 9px;
		background: var(--ds-surface-3);
		border: 1px solid var(--ds-border);
	}
	.cols-seg-btn {
		min-width: 30px;
		height: 26px;
		padding: 0 8px;
		border-radius: 7px;
		font-size: 13px;
		font-weight: 500;
		color: var(--ds-text-dim);
		background: transparent;
		transition:
			background 0.12s,
			color 0.12s,
			box-shadow 0.12s;
	}
	.cols-seg-btn:hover:not(.active) {
		color: var(--ds-text);
		background: var(--ds-surface);
	}
	.cols-seg-btn.active {
		color: var(--ds-text);
		background: var(--ds-surface);
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
	}
	.cols-seg-btn:focus-visible {
		outline: none;
		box-shadow: 0 0 0 2px var(--ds-accent-dim);
	}
</style>
