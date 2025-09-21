<script lang="ts">
	import { browser } from '$app/environment';
	import { Input } from 'flowbite-svelte';
	import { onDestroy, onMount, type Component, type ComponentType } from 'svelte';

	type Option = {
		label: string;
		value: string;
		icon?: Component | ComponentType;
	};

	interface Props {
		value?: string;
		options?: Option[];
		allowCustomValues?: boolean;
		defaultIcon?: (value: string) => Component | ComponentType | undefined;
		onChange?: (value: string) => void;
		dropdownClass?: string;
	}

	let {
		value = $bindable(''),
		options = [],
		allowCustomValues = false,
		defaultIcon,
		onChange,
		dropdownClass = ''
	}: Props = $props();

	let isOpen = $state(false);
	let highlightedIndex = $state(-1);
	let parent = $state<HTMLElement | null>(null);

	const filteredOptions = $derived.by(() => {
		const keys = value.split(' ').map((k) => k.trim().toLowerCase());
		return options.filter((item) => keys.every((key) => item.label.toLowerCase().includes(key)));
	});

	const selectItem = (item: Option) => {
		value = item.value;
		onChange?.(item.value);
		highlightedIndex = -1;
		isOpen = false;
	};

	const openDropdown = (e: Event) => {
		e.preventDefault();
		e.stopPropagation();
		isOpen = true;
	};

	const closeDropdown = () => {
		isOpen = false;
	};

	onMount(() => {
		if (browser) document.addEventListener('click', closeDropdown);
	});

	onDestroy(() => {
		if (browser) document.removeEventListener('click', closeDropdown);
	});

	const onKeyDown = (event: KeyboardEvent) => {
		if (!isOpen) return;

		if (event.key === 'ArrowDown') {
			event.preventDefault();
			event.stopPropagation();
			highlightedIndex = (highlightedIndex + 1) % filteredOptions.length;
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			event.stopPropagation();
			highlightedIndex = (highlightedIndex - 1 + filteredOptions.length) % filteredOptions.length;
		} else if (event.key === 'Enter' && highlightedIndex >= 0) {
			event.preventDefault();
			selectItem(filteredOptions[highlightedIndex]);
		}
	};

	const isOption = (value: string) => {
		return options.some((v) => v.value === value);
	};

	const floatingStyle = $derived.by(() => {
		if (!parent) return '';
		const rect = parent.getBoundingClientRect();
		return `position: fixed; left: ${rect.left}px; width: ${rect.right - rect.left}px;`;
	});
</script>

<div class="relative" bind:this={parent}>
	<Input
		bind:value
		on:change={() => {
			if (allowCustomValues || isOption(value)) {
				onChange?.(value);
			}
		}}
		on:input={() => {
			if (allowCustomValues || isOption(value)) {
				onChange?.(value);
			}
		}}
		on:click={openDropdown}
		on:focus={openDropdown}
		on:keydown={onKeyDown}
	>
		<div slot="left">
			{@const Icon = options?.find((item) => item.value === value)?.icon}
			{@const DefaultIcon = defaultIcon?.(value)}
			{#if Icon}
				<Icon class="h-4 w-4 text-gray-900 dark:text-white" />
			{:else if DefaultIcon}
				<DefaultIcon class="h-4 w-4 text-gray-900 dark:text-white" />
			{/if}
		</div>
	</Input>
	{#if isOpen && filteredOptions.length > 0}
		<div
			id="dropdown-list"
			class="w-full max-h-[19rem] overflow-y-auto bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-base border border-gray-300 dark:border-gray-700 rounded-lg shadow-md mt-1 z-10 {dropdownClass}"
			role="listbox"
			style={floatingStyle}
		>
			{#each filteredOptions as item, index}
				{@const highlightedClass = index === highlightedIndex ? 'bg-gray-200 dark:bg-gray-600' : ''}
				{@const selectedClass =
					item.value === value ? 'text-primary-600 dark:text-primary-400' : ''}
				{@const Icon = item.icon}
				<option
					class="p-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-600 {highlightedClass} {selectedClass}"
					onclick={() => selectItem(item)}
					onkeydown={(event) => {
						if (event.key === 'Enter') {
							event.preventDefault();
							selectItem(item);
							isOpen = false;
						}
					}}
					tabindex="-1"
				>
					{#if Icon}
						<Icon class="inline h-4 w-4 mr-2" />
					{/if}
					{item.label}
				</option>
			{/each}
		</div>
	{/if}
</div>
