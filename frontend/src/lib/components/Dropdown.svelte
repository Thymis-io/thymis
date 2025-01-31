<script lang="ts">
	import { browser } from '$app/environment';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { onDestroy, onMount } from 'svelte';

	export let values: (string | number)[] = [];
	export let selected: string | number | null = null;
	export let showBox: boolean = true;
	export let onSelected: (item: string | number) => void = () => {};

	let divClass: string = 'w-64';
	let isOpen = false;
	let highlightedIndex = -1;

	const toggleDropdown = () => {
		isOpen = !isOpen;
	};

	const closeDropdown = () => {
		isOpen = false;
	};

	const selectItem = (item: string | number) => {
		selected = item;
		isOpen = false;
		onSelected(item);
	};

	const onKeyDown = (event: KeyboardEvent) => {
		if (!isOpen) return;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			event.stopPropagation();
			highlightedIndex = (highlightedIndex + 1) % values.length;
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			event.stopPropagation();
			highlightedIndex = (highlightedIndex - 1 + values.length) % values.length;
		} else if (event.key === 'Enter' && highlightedIndex >= 0) {
			event.preventDefault();
			selectItem(values[highlightedIndex]);
		}
	};

	onMount(() => {
		if (browser) document.addEventListener('click', closeDropdown);
	});

	onDestroy(() => {
		if (browser) document.removeEventListener('click', closeDropdown);
	});

	export { divClass as class };
</script>

<div
	class="relative {divClass}"
	on:keydown={onKeyDown}
	role="combobox"
	aria-haspopup="listbox"
	aria-expanded={isOpen}
	aria-controls="dropdown-list"
	tabindex="0"
>
	<button
		class="w-full flex justify-between items-center p-1 {showBox &&
			'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg shadow-sm'}"
		on:click={(e) => {
			e.preventDefault();
			e.stopPropagation();
			toggleDropdown();
		}}
		aria-controls="dropdown-list"
	>
		<slot>{selected || 'Select an option'}</slot>
		<ChevronDown class="h-4 w-4" />
	</button>

	{#if isOpen}
		<div
			id="dropdown-list"
			class="absolute w-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg shadow-md mt-1 z-10"
			role="listbox"
		>
			{#each values as item, index}
				{@const highlightedClass = index === highlightedIndex ? 'bg-gray-200 dark:bg-gray-600' : ''}
				{@const selectedClass = item === selected ? 'text-primary-600 dark:text-primary-400' : ''}
				<option
					class="p-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 {highlightedClass} {selectedClass}"
					on:click={() => selectItem(item)}
					on:keydown={(event) => {
						if (event.key === 'Enter') {
							event.preventDefault();
							selectItem(item);
							toggleDropdown();
						}
					}}
					tabindex="-1"
				>
					{item}
				</option>
			{/each}
		</div>
	{/if}
</div>
