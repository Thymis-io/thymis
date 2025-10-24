<script lang="ts" generics="T extends string | number">
	import { browser } from '$app/environment';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { onDestroy, onMount, type Component, type ComponentType, type Snippet } from 'svelte';

	interface Props {
		values?: { label: string; icon: Component | ComponentType; value: T }[];
		selected?: T | null;
		disabled?: boolean;
		showBox?: boolean;
		placeholder?: string;
		onSelected?: (item: T) => T | null;
		class?: string;
		innerClass?: string;
		dropdownClass?: string;
		children?: Snippet;
		options?: Snippet;
	}

	let {
		values = [],
		selected = $bindable(null),
		disabled = false,
		showBox = true,
		placeholder = 'Select an option',
		onSelected = (item) => item,
		class: divClass = 'w-64',
		innerClass = '',
		dropdownClass = '',
		children,
		options
	}: Props = $props();
	let isOpen = $state(false);
	let highlightedIndex = $state(-1);

	const toggleDropdown = () => {
		isOpen = !isOpen;
	};

	const closeDropdown = () => {
		isOpen = false;
	};

	const selectItem = (item: { label: string; value: T }) => {
		selected = onSelected(item.value);
		isOpen = false;
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
</script>

<div
	class="relative {divClass}"
	onkeydown={onKeyDown}
	role="combobox"
	aria-haspopup="listbox"
	aria-expanded={isOpen}
	aria-controls="dropdown-list"
	tabindex="0"
>
	<button
		class="w-full flex justify-between items-center p-1 disabled:opacity-50 disabled:cursor-not-allowed {showBox &&
			'bg-gray-50 dark:bg-gray-600 text-gray-900 dark:text-white border border-gray-300 dark:border-gray-500 rounded-lg shadow-sm'} {innerClass}"
		onclick={(e) => {
			e.preventDefault();
			e.stopPropagation();
			toggleDropdown();
		}}
		{disabled}
		aria-controls="dropdown-list"
	>
		{#if children}
			{@render children()}
		{:else if selected}
			{@const item = values.find((v) => v.value === selected)}
			{@const Icon = item?.icon}
			<div class="flex items-center gap-1">
				{#if Icon}
					<Icon class="w-4 h-4 shrink-0" />
				{/if}
				{item?.label || placeholder}
			</div>
		{:else}
			{selected || placeholder}
		{/if}
		<ChevronDown class="h-4 w-4 ml-1" />
	</button>

	{#if isOpen}
		<div
			id="dropdown-list"
			class="absolute w-full max-h-[19rem] overflow-y-auto bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-base border border-gray-300 dark:border-gray-700 rounded-lg shadow-md mt-1 z-10 {dropdownClass}"
			role="listbox"
		>
			{#each values as item, index (item.value)}
				{@const highlightedClass = index === highlightedIndex ? 'bg-gray-200 dark:bg-gray-600' : ''}
				{@const selectedClass =
					item.value === selected ? 'text-primary-600 dark:text-primary-400' : ''}
				{@const Icon = item.icon}
				<option
					class="flex items-center gap-1 p-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 {highlightedClass} {selectedClass}"
					onclick={() => selectItem(item)}
					onkeydown={(event) => {
						if (event.key === 'Enter') {
							event.preventDefault();
							selectItem(item);
							toggleDropdown();
						}
					}}
					tabindex="-1"
				>
					{#if Icon}
						<Icon class="h-4 w-4" />
					{/if}
					{item.label}
				</option>
			{/each}
			{#if options}
				{@render options()}
			{/if}
		</div>
	{/if}
</div>
