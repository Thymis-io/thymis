<script lang="ts">
	import { Input, Button, Dropdown, DropdownItem } from 'flowbite-svelte';
	import { CalendarIcon, ChevronDownIcon } from 'lucide-svelte';

	interface Props {
		value?: string;
		onChange?: (newValue: string) => void;
	}

	let { value = $bindable(''), onChange = () => {} }: Props = $props();

	// Predefined common expressions
	const commonExpressions = [
		{ label: 'Daily (every day at midnight)', value: 'daily' },
		{ label: 'Weekly (every Monday at midnight)', value: 'weekly' },
		{ label: 'Monthly (first day of month)', value: 'monthly' },
		{ label: 'Yearly (January 1st)', value: 'yearly' },
		{ label: 'Hourly (every hour)', value: 'hourly' },
		{ label: 'Every 15 minutes', value: '*-*-* *:0/15' },
		{ label: 'Every Monday at 9 AM', value: 'Mon *-*-* 09:00:00' },
		{ label: 'Daily at midnight', value: '*-*-* 00:00:00' },
		{ label: 'Weekdays at 6 PM', value: 'Mon..Fri *-*-* 18:00:00' },
		{ label: 'Weekends at 10 AM', value: 'Sat,Sun *-*-* 10:00:00' },
		{ label: 'Every 2 hours', value: '*-*-* */2:00:00' },
		{ label: 'Business hours (9-5)', value: '*-*-* 09..17:00:00' },
		{ label: 'First day of month at 2 AM', value: '*-*-01 02:00:00' },
		{ label: 'Weekdays every 30 minutes', value: 'Mon..Fri *-*-* *:0/30' }
	];

	const selectExpression = (selectedValue: string) => {
		value = selectedValue;
		onChange(selectedValue);
	};
</script>

<div class="flex gap-2 w-full">
	<Input
		bind:value
		placeholder="[DayOfWeek] Year-Month-Day Hour:Minute:Second (e.g., Mon *-*-* 09:00:00)"
		on:input={(e) => onChange(e.target?.value as string)}
		class="flex-1"
	/>
	<Button color="alternative" class="px-3">
		<CalendarIcon size={16} />
		<ChevronDownIcon size={16} class="ml-1" />
	</Button>
	<Dropdown class="w-64">
		{#each commonExpressions as expr}
			<DropdownItem on:click={() => selectExpression(expr.value)}>
				{expr.label}
			</DropdownItem>
		{/each}
	</Dropdown>
</div>
