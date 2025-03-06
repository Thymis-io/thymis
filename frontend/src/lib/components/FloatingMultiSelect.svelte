<script lang="ts">
	import { MultiSelect, type Option } from 'svelte-multiselect';
	import { onDestroy, onMount, type Snippet } from 'svelte';

	type T = $$Generic<Option>;

	interface Props {
		options: T[];
		selected: T[];
		outerDivClass: string;
		children?: Snippet<[{ option: T }]>;
	}

	let { options, selected = $bindable(), outerDivClass, children }: Props = $props();

	let multiSelectDiv: HTMLDivElement | null = $state(null);
	let multiSelectRect: DOMRect | null = $state(null);
	let multiSelectResizeObserver: ResizeObserver | null = null;
	let multiSelectMutationObserver: MutationObserver | null = null;

	const multiSelectUpdateRect = () => {
		if (multiSelectDiv) {
			multiSelectRect = multiSelectDiv.getBoundingClientRect();
		}
	};

	const multiSelectSetupObservers = (multiSelectDiv: HTMLDivElement | null) => {
		if (!multiSelectDiv) return;
		multiSelectUpdateRect();
		multiSelectCleanupObservers();
		multiSelectResizeObserver = new ResizeObserver(multiSelectUpdateRect);
		multiSelectResizeObserver.observe(multiSelectDiv);
		multiSelectMutationObserver = new MutationObserver(multiSelectUpdateRect);
		multiSelectMutationObserver.observe(multiSelectDiv, { attributes: true, subtree: true });
	};

	const multiSelectCleanupObservers = () => {
		multiSelectResizeObserver?.disconnect();
		multiSelectMutationObserver?.disconnect();
	};

	onMount(() => {
		multiSelectSetupObservers(multiSelectDiv);
	});

	onDestroy(multiSelectCleanupObservers);

	const children_render = $derived(children);
</script>

<MultiSelect
	bind:outerDiv={multiSelectDiv}
	ulOptionsStyle={`position: fixed; top: ${multiSelectRect?.bottom}px; left: ${multiSelectRect?.left}px; width: ${multiSelectRect?.width}px; max-height: var(--sms-options-max-height);`}
	{options}
	bind:selected
	{outerDivClass}
>
	{#snippet children({ option }: { option: T })}
		{@render children_render?.({ option })}
	{/snippet}
</MultiSelect>
