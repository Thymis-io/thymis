<script lang="ts">
	import { Input, Button, Dropdown, DropdownItem, Tooltip } from 'flowbite-svelte';
	import CalendarIcon from 'lucide-svelte/icons/calendar';
	import ChevronDownIcon from 'lucide-svelte/icons/chevron-down';
	import CheckCircleIcon from 'lucide-svelte/icons/check-circle';
	import XCircleIcon from 'lucide-svelte/icons/x-circle';
	import { t } from 'svelte-i18n';

	interface Props {
		value?: string;
		onChange?: (newValue: string) => void;
	}

	let { value = $bindable(''), onChange = () => {} }: Props = $props();

	let validationState: 'valid' | 'invalid' | 'pending' | null = $state(null);
	let validationError = $state('');
	let validationResult: string[] | null = $state(null);
	let debounceTimer: number | null = null;

	const commonExpressions = [
		{ label: $t('systemd.calendar.templates.hourly'), value: 'hourly' },
		{ label: $t('systemd.calendar.templates.daily'), value: 'daily' },
		{ label: $t('systemd.calendar.templates.weekly'), value: 'weekly' },
		{ label: $t('systemd.calendar.templates.monthly'), value: 'monthly' },
		{ label: $t('systemd.calendar.templates.yearly'), value: 'yearly' },
		{ label: $t('systemd.calendar.templates.every-15-minutes'), value: '*-*-* *:0/15' },
		{ label: $t('systemd.calendar.templates.monday-9am'), value: 'Mon *-*-* 09:00:00' },
		{ label: $t('systemd.calendar.templates.daily-midnight'), value: '*-*-* 00:00:00' },
		{ label: $t('systemd.calendar.templates.weekdays-6pm'), value: 'Mon..Fri *-*-* 18:00:00' },
		{ label: $t('systemd.calendar.templates.weekends-10am'), value: 'Sat,Sun *-*-* 10:00:00' },
		{ label: $t('systemd.calendar.templates.every-2-hours'), value: '*-*-* 00/2:00:00' },
		{ label: $t('systemd.calendar.templates.business-hours'), value: '*-*-* 09..17:00:00' },
		{ label: $t('systemd.calendar.templates.monthly-1st-2am'), value: '*-*-01 02:00:00' },
		{ label: $t('systemd.calendar.templates.weekdays-30min'), value: 'Mon..Fri *-*-* *:0/30' }
	];

	const validateCalendar = async (inputValue: string) => {
		if (!inputValue.trim()) {
			validationState = null;
			validationResult = null;
			return;
		}

		validationState = 'pending';
		try {
			const response = await fetch(
				`/api/config/check-systemd-timer?timer_type=calendar&value=${encodeURIComponent(inputValue)}&iterations=5`
			);
			const result = await response.json();

			if (response.ok) {
				validationState = 'valid';
				validationResult = result;
			} else {
				validationState = 'invalid';
				validationError = result.detail || 'Invalid calendar expression';
				validationResult = null;
			}
		} catch {
			validationState = 'invalid';
			validationError = $t('systemd.calendar.tooltip.validation-failed');
			validationResult = null;
		}
	};

	const debouncedValidate = (inputValue: string) => {
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}
		debounceTimer = setTimeout(() => validateCalendar(inputValue), 500);
	};

	const selectExpression = (selectedValue: string) => {
		value = selectedValue;
		onChange(selectedValue);
		validateCalendar(selectedValue);
	};

	// Validate when value changes
	$effect(() => {
		debouncedValidate(value);
	});
</script>

<div class="flex gap-2">
	<div class="relative flex-1">
		<Input
			bind:value
			placeholder={$t('systemd.calendar.placeholder')}
			on:input={(e) => onChange(e.target?.value as string)}
			class="flex-1"
		/>
		{#if validationState === 'valid'}
			<CheckCircleIcon
				class="absolute right-2 top-1/2 transform -translate-y-1/2 text-green-500"
				size={16}
				id="calendar-valid-icon"
			/>
			<Tooltip
				triggeredBy="#calendar-valid-icon"
				class="w-96 text-base text-gray-900 dark:text-white"
			>
				{#if validationResult?.length}
					<div class="text-sm">
						<div class="font-medium mb-2">{$t('systemd.calendar.tooltip.next-occurrences')}</div>
						<ul class="space-y-1">
							{#each validationResult as date}
								<li class="font-mono text-xs">{date}</li>
							{/each}
						</ul>
					</div>
				{/if}
			</Tooltip>
		{:else if validationState === 'invalid'}
			<XCircleIcon
				class="absolute right-2 top-1/2 transform -translate-y-1/2 text-red-500"
				size={16}
				id="calendar-invalid-icon"
			/>
			<Tooltip
				triggeredBy="#calendar-invalid-icon"
				class="w-96 text-base text-gray-900 dark:text-white"
			>
				{validationError}
			</Tooltip>
		{/if}
	</div>
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
