<script lang="ts">
	import { MultiSelect, type Option } from 'svelte-multiselect';
	import { onDestroy } from 'svelte';

	type T = $$Generic<Option>;
	const toT = (option: Option): T => option as T;

	export let options: T[];
	export let selected: T[];
	export let outerDivClass: string;

	let multiSelectDiv: HTMLDivElement | null = null;
	let multiSelectRect: DOMRect | null = null;
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

	$: multiSelectSetupObservers(multiSelectDiv);
	onDestroy(multiSelectCleanupObservers);
</script>

<MultiSelect
	bind:outerDiv={multiSelectDiv}
	ulOptionsStyle={`position: fixed; top: ${multiSelectRect?.bottom}px; left: ${multiSelectRect?.left}px; width: ${multiSelectRect?.width}px; max-height: var(--sms-options-max-height);`}
	{options}
	bind:selected
	{outerDivClass}
	let:option
>
	<slot option={toT(option)} />
</MultiSelect>
