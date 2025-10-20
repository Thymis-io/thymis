<script lang="ts">
	import { Input, Button, Dropdown, DropdownItem } from 'flowbite-svelte';
	import { ClockIcon, ChevronDownIcon } from 'lucide-svelte';

	interface Props {
		value?: string;
		onChange?: (newValue: string) => void;
	}

	let { value = $bindable(''), onChange = () => {} }: Props = $props();

	// Predefined common time spans
	const commonTimeSpans = [
		{ label: '30 seconds', value: '30s' },
		{ label: '5 minutes', value: '5min' },
		{ label: '30 minutes', value: '30min' },
		{ label: '1 hour', value: '1h' },
		{ label: '1 hour 30 minutes', value: '1h 30min' },
		{ label: '6 hours', value: '6h' },
		{ label: '1 day', value: '1d' },
		{ label: '1 week', value: '1w' },
		{ label: '1 month', value: '1M' }
	];

	const selectTimeSpan = (selectedValue: string) => {
		value = selectedValue;
		onChange(selectedValue);
	};
</script>

<div class="flex gap-2">
	<Input
		bind:value
		placeholder="Time span (e.g., 30s, 5min, 2h, 1d, 1w)"
		on:input={(e) => onChange(e.target?.value as string)}
		class="flex-1"
	/>
	<Button color="alternative" class="px-3">
		<ClockIcon size={16} />
		<ChevronDownIcon size={16} class="ml-1" />
	</Button>
	<Dropdown class="w-48">
		{#each commonTimeSpans as timeSpan}
			<DropdownItem on:click={() => selectTimeSpan(timeSpan.value)}>
				{timeSpan.label}
			</DropdownItem>
		{/each}
	</Dropdown>
</div>
